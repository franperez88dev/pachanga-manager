"""Partidos.

Ciclo de vida de un partido:
  1. (admin) Lo crea, con fecha, lugar y un texto con el precio.
  2. (jugadores) Cada uno RESERVA SU HUECO. Los 10 primeros juegan; los siguientes son
     reservas. Se puede LIBERAR el hueco: con menos de 24 horas para el partido lleva multa.
     Si un titular se va, el primer reserva sube solo.
  3. (admin) Crea los equipos con los 10 primeros (una sola vez). Desde ahí la lista queda
     cerrada para los jugadores: solo el admin puede quitar o añadir a alguien (y entonces
     los equipos y la votación empiezan de cero).
     Los que juegan votan (una vez) si quieren otro reparto; con 6 síes el admin puede
     rebarajar, hasta 3 repartos en total.
  4. (admin) Cierra indicando el resultado. Desde aquí cuenta como partido jugado.
  5. Goles y gpp, por uno de dos caminos (o una mezcla):
     a) El admin rellena la planilla en ese momento: queda todo confirmado.
     b) El admin pulsa "Sig." y cada jugador apunta lo suyo desde su móvil;
        el admin lo confirma o lo descarta cuando pueda.
"""
import random
from datetime import datetime

from flask import Blueprint, current_app, g, jsonify
from sqlalchemy.exc import IntegrityError

from ..equipos import JUGADORES_POR_PARTIDO, elegir_reparto
from ..errores import ErrorApi
from ..extensions import db
from ..models import (
    EQUIPO_BLANCO, EQUIPO_NEGRO, PARTIDO_ABIERTO, PARTIDO_CERRADO, REPORTE_CONFIRMADO,
    REPORTE_PENDIENTE, REPORTES_ACTIVOS, Match, MatchPlayer, Multa, StatReport, User, VotoRebarajar,
)
from ..serializadores import partido_detalle, partido_resumen, reporte, usuario_publico
from ..seguridad import requiere_admin, requiere_aprobado
from ..servicios import (
    avisos_marcador, con_reporte, deshacer_equipos, exceso_marcador, fuerzas_de, lleva_multa,
    poner_multa, stats_confirmadas_del_partido,
)
from . import cuerpo_json, entero

bp = Blueprint("partidos", __name__, url_prefix="/api/partidos")

MAX_GOLES_JUGADOR = 30
MAX_GOLES_EQUIPO = 99
CAMPOS_STATS = ("goles", "gpp", "asistencias")
# De momento la app no usa asistencias (ver DECISIONES.md): son opcionales y valen 0 si no llegan.
CAMPOS_OPCIONALES = ("gpp", "asistencias")


def leer_stats(datos):
    datos = {c: 0 for c in CAMPOS_OPCIONALES} | datos
    return {c: entero(datos, c, 0, MAX_GOLES_JUGADOR) for c in CAMPOS_STATS}


def partido_o_404(pid):
    partido = db.session.get(Match, pid)
    if partido is None:
        raise ErrorApi(404, "Partido no encontrado")
    return partido


def exigir_abierto(partido):
    if not partido.abierto:
        raise ErrorApi(409, "El partido está cerrado y ya no se puede modificar")


def exigir_cerrado(partido):
    if partido.abierto:
        raise ErrorApi(409, "Los goles y asistencias se apuntan cuando el partido está cerrado")


def leer_datos_partido(datos, parcial=False):
    """Valida 'fecha' (formato 2026-10-04T19:00), 'lugar' e 'info_pago' (texto libre del precio,
    opcional). Con parcial=True solo se tocan los campos que vengan."""
    cambios = {}
    if "fecha" in datos or not parcial:
        try:
            cambios["fecha"] = datetime.fromisoformat(str(datos.get("fecha", ""))).replace(
                tzinfo=None, second=0, microsecond=0)
        except ValueError:
            raise ErrorApi(400, "Fecha no válida. Formato: 2026-10-04T19:00")
    if "lugar" in datos or not parcial:
        lugar = " ".join(str(datos.get("lugar") or "").split())
        if not 1 <= len(lugar) <= 80:
            raise ErrorApi(400, "Escribe el lugar (máximo 80 caracteres)")
        cambios["lugar"] = lugar
    if "info_pago" in datos:
        info = " ".join(str(datos.get("info_pago") or "").split())
        if len(info) > 200:
            raise ErrorApi(400, "El texto del precio no puede pasar de 200 caracteres")
        cambios["info_pago"] = info or None
    return cambios


def leer_resultado(partido):
    datos = cuerpo_json()
    partido.goles_blanco = entero(datos, "goles_blanco", 0, MAX_GOLES_EQUIPO)
    partido.goles_negro = entero(datos, "goles_negro", 0, MAX_GOLES_EQUIPO)


def mi_plaza(partido, usuario_id):
    return next((mp for mp in partido.jugadores if mp.user_id == usuario_id), None)


def juega(partido, usuario_id):
    """¿Es de los 10 que juegan (titular)?"""
    return any(mp.user_id == usuario_id for mp in partido.titulares)


# ------------------------------------------------------------ consulta (jugadores)
@bp.get("")
@requiere_aprobado
def lista():
    partidos = Match.query.order_by(Match.fecha.desc()).all()
    return jsonify(partidos=[partido_resumen(p, g.usuario) for p in partidos])


@bp.get("/proximo")
@requiere_aprobado
def proximo():
    """El partido abierto más cercano en fecha (o null si no hay ninguno)."""
    p = Match.query.filter_by(estado=PARTIDO_ABIERTO).order_by(Match.fecha.asc()).first()
    return jsonify(partido=partido_detalle(p, g.usuario) if p else None)


@bp.get("/<int:pid>")
@requiere_aprobado
def detalle(pid):
    return jsonify(partido=partido_detalle(partido_o_404(pid), g.usuario))


# ------------------------------------------------------------ crear y editar (admin)
@bp.post("")
@requiere_admin
def crear():
    partido = Match(**leer_datos_partido(cuerpo_json()))
    db.session.add(partido)
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario)), 201


@bp.patch("/<int:pid>")
@requiere_admin
def editar(pid):
    """Cambiar fecha, lugar o el texto del precio mientras el partido esté abierto."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    for campo, valor in leer_datos_partido(cuerpo_json(), parcial=True).items():
        setattr(partido, campo, valor)
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


@bp.delete("/<int:pid>")
@requiere_admin
def borrar(pid):
    partido = partido_o_404(pid)
    exigir_abierto(partido)  # un partido abierto aún no tiene goles apuntados
    VotoRebarajar.query.filter_by(match_id=partido.id).delete(synchronize_session=False)
    # Si el partido se cancela, sus multas dejan de tener sentido
    Multa.query.filter_by(match_id=partido.id).delete(synchronize_session=False)
    db.session.delete(partido)
    db.session.commit()
    return "", 204


# ------------------------------------------------------------ reservar y liberar hueco (jugadores)
@bp.post("/<int:pid>/hueco")
@requiere_aprobado
def reservar_hueco(pid):
    """El jugador se apunta. Si ya hay 10, entra como reserva (por orden de llegada)."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    if partido.equipos_generados:
        raise ErrorApi(409, "Los equipos ya están hechos y la lista está cerrada. Habla con el admin")
    if mi_plaza(partido, g.usuario.id):
        raise ErrorApi(409, "Ya estás apuntado a este partido")
    partido.jugadores.append(MatchPlayer(user_id=g.usuario.id))
    try:
        db.session.commit()
    except IntegrityError:  # dos toques casi a la vez
        db.session.rollback()
        raise ErrorApi(409, "Ya estás apuntado a este partido")
    return jsonify(partido=partido_detalle(partido, g.usuario)), 201


@bp.delete("/<int:pid>/hueco")
@requiere_aprobado
def liberar_hueco(pid):
    """El jugador se borra. Un titular que se borra con menos de 24 horas para el partido
    se lleva una multa (aunque un reserva ocupe su sitio). Los reservas se borran sin multa."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    plaza = mi_plaza(partido, g.usuario.id)
    if plaza is None:
        raise ErrorApi(409, "No estás apuntado a este partido")
    if partido.equipos_generados:
        raise ErrorApi(409, "Los equipos ya están hechos y la lista está cerrada. Si no puedes ir, avisa al admin")

    multado = juega(partido, g.usuario.id) and lleva_multa(partido)
    if multado:
        poner_multa(partido, g.usuario.id, "Hueco liberado con menos de 24 horas para el partido")
    partido.jugadores.remove(plaza)  # si había reservas, el primero pasa a estar entre los 10
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario), multa=multado)


# ------------------------------------------------------------ gestionar la lista (admin)
@bp.post("/<int:pid>/jugadores")
@requiere_admin
def apuntar_jugador(pid):
    """El admin apunta a alguien ({"user_id": 7}), p. ej. a quien no usa la app.
    Entra al final de la lista, como cualquiera. Si los equipos ya estaban hechos, entra como reserva."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    uid = entero(cuerpo_json(), "user_id", 1, 2**31 - 1)
    usuario = db.session.get(User, uid)
    if usuario is None or not usuario.aprobado:
        raise ErrorApi(404, "Jugador no encontrado")
    if mi_plaza(partido, uid):
        raise ErrorApi(409, f"{usuario.mote} ya está apuntado")
    partido.jugadores.append(MatchPlayer(user_id=uid))
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario)), 201


@bp.delete("/<int:pid>/jugadores/<int:uid>")
@requiere_admin
def quitar_jugador(pid, uid):
    """El admin quita a alguien de la lista. Con {"multa": true} le deja una multa apuntada.
    Si era de los que jugaban y los equipos ya estaban hechos, los equipos y la votación
    se deshacen: el primer reserva pasa a jugar y hay que volver a crear los equipos."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    plaza = mi_plaza(partido, uid)
    if plaza is None:
        raise ErrorApi(404, "Ese jugador no está apuntado a este partido")
    jugaba = juega(partido, uid)
    if cuerpo_json().get("multa") is True:
        poner_multa(partido, uid, "Quitado del partido por el admin, con multa")
    partido.jugadores.remove(plaza)
    if jugaba and partido.equipos_generados:
        db.session.flush()
        deshacer_equipos(partido)
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


# ------------------------------------------------------------ equipos y votación
def votos_si(partido):
    return VotoRebarajar.query.filter_by(
        match_id=partido.id, ronda=partido.num_repartos, cambiar=True).count()


@bp.post("/<int:pid>/equipos")
@requiere_admin
def crear_equipos(pid):
    """{"rebarajar": false} -> "Crear equipos" con los 10 primeros apuntados: el reparto más
                            igualado. Solo una vez. La lista queda cerrada para los jugadores.
    {"rebarajar": true}  -> otro reparto equilibrado distinto del actual. Solo si lo
                            han votado (6 síes) y sin pasar de 3 repartos en total."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    cfg = current_app.config

    anterior = None
    if cuerpo_json().get("rebarajar") is True:
        if not partido.equipos_generados:
            raise ErrorApi(409, "Todavía no hay equipos que rebarajar")
        if partido.num_repartos >= cfg["MAX_REPARTOS"]:
            raise ErrorApi(409, f"Ya se han hecho los {cfg['MAX_REPARTOS']} repartos permitidos")
        if votos_si(partido) < cfg["VOTOS_PARA_REBARAJAR"]:
            raise ErrorApi(409, f"Para rebarajar hacen falta {cfg['VOTOS_PARA_REBARAJAR']} votos a favor")
        anterior = (
            {mp.user_id for mp in partido.jugadores if mp.equipo == EQUIPO_BLANCO},
            {mp.user_id for mp in partido.jugadores if mp.equipo == EQUIPO_NEGRO},
        )
    elif partido.equipos_generados:
        raise ErrorApi(409, "Los equipos ya están hechos. Solo se pueden rehacer si lo votan los jugadores")

    juegan = partido.titulares  # con equipos: los que ya juegan; sin equipos: los 10 primeros
    if len(juegan) != JUGADORES_POR_PARTIDO:
        raise ErrorApi(409, f"Hacen falta {JUGADORES_POR_PARTIDO} jugadores apuntados (hay {len(juegan)})")

    fuerzas = fuerzas_de([mp.user_id for mp in juegan])
    blanco, _negro, f_blanco, f_negro = elegir_reparto(fuerzas, anterior=anterior,
                                                       tolerancia=cfg["TOLERANCIA_REBARAJAR"])
    for mp in juegan:
        mp.equipo = EQUIPO_BLANCO if mp.user_id in blanco else EQUIPO_NEGRO
    sortear_posiciones(juegan)
    partido.equipos_generados = True
    partido.num_repartos += 1  # empieza una ronda de votación nueva (los votos viejos ya no cuentan)
    partido.fuerza_blanco = f_blanco
    partido.fuerza_negro = f_negro
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


def sortear_posiciones(juegan):
    """En cada equipo se sortea quién juega dónde (0 portero, 1-2 defensas, 3-4 delanteros)
    y el orden en la portería: empieza el que sale de portero y el resto, al azar."""
    azar = random.SystemRandom()
    for color in (EQUIPO_BLANCO, EQUIPO_NEGRO):
        suyos = azar.sample([mp for mp in juegan if mp.equipo == color], JUGADORES_POR_PARTIDO // 2)
        for posicion, mp in enumerate(suyos):
            mp.posicion = posicion
        portero, resto = suyos[0], azar.sample(suyos[1:], len(suyos) - 1)
        for turno, mp in enumerate([portero] + resto, start=1):
            mp.orden_porteria = turno


@bp.post("/<int:pid>/voto")
@requiere_aprobado
def votar(pid):
    """{"cambiar": true|false}: "¿Deseas una nueva selección de equipo?".
    Solo los que juegan, con los equipos hechos y si aún quedan repartos.
    Se vota UNA vez por reparto y no se puede cambiar; si el admin rebaraja,
    empieza una votación nueva y cada uno puede votar otra vez."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    if not partido.equipos_generados:
        raise ErrorApi(409, "Todavía no hay equipos")
    if not juega(partido, g.usuario.id):
        raise ErrorApi(403, "Solo votan los que juegan este partido")
    if partido.num_repartos >= current_app.config["MAX_REPARTOS"]:
        raise ErrorApi(409, "Ya no se pueden rehacer más los equipos")
    cambiar = cuerpo_json().get("cambiar")
    if not isinstance(cambiar, bool):
        raise ErrorApi(400, "'cambiar' debe ser true o false")

    ya_votado = "Ya has votado. Podrás volver a votar si el admin hace un nuevo reparto"
    if db.session.get(VotoRebarajar, (partido.id, g.usuario.id, partido.num_repartos)):
        raise ErrorApi(409, ya_votado)
    db.session.add(VotoRebarajar(match_id=partido.id, user_id=g.usuario.id,
                                 ronda=partido.num_repartos, cambiar=cambiar))
    try:
        db.session.commit()
    except IntegrityError:  # dos toques casi a la vez: la clave primaria impide el voto doble
        db.session.rollback()
        raise ErrorApi(409, ya_votado)
    return jsonify(partido=partido_detalle(partido, g.usuario))


# ------------------------------------------------------------ después del partido (admin)
@bp.post("/<int:pid>/cerrar")
@requiere_admin
def cerrar(pid):
    """Recibe {"goles_blanco": 5, "goles_negro": 3}."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    if not partido.equipos_generados:
        raise ErrorApi(409, "No se puede cerrar un partido sin equipos")
    leer_resultado(partido)
    partido.estado = PARTIDO_CERRADO
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


@bp.put("/<int:pid>/resultado")
@requiere_admin
def corregir_resultado(pid):
    """Por si el admin se equivocó al poner el resultado."""
    partido = partido_o_404(pid)
    exigir_cerrado(partido)
    leer_resultado(partido)
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


def planilla(partido):
    """Estado de los goles de cada jugador del partido: lo confirmado y lo que tenga pendiente."""
    reportes = StatReport.query.filter(
        StatReport.match_id == partido.id, StatReport.estado.in_(REPORTES_ACTIVOS)).all()
    confirmados, pendientes = {}, {}
    for r in reportes:
        destino = confirmados if r.estado == REPORTE_CONFIRMADO else pendientes
        fila = destino.setdefault(r.user_id, {c: 0 for c in CAMPOS_STATS})
        for c in CAMPOS_STATS:
            fila[c] += getattr(r, c)

    cero = {c: 0 for c in CAMPOS_STATS}
    orden = sorted(partido.titulares, key=lambda mp: (mp.equipo != EQUIPO_BLANCO, mp.usuario.mote.casefold()))
    jugadores = [
        {**usuario_publico(mp.usuario), "equipo": mp.equipo,
         **confirmados.get(mp.user_id, cero), "pendiente": pendientes.get(mp.user_id)}
        for mp in orden
    ]
    return {
        "resultado": {"blanco": partido.goles_blanco, "negro": partido.goles_negro},
        "jugadores": jugadores,
        "avisos": avisos_marcador(partido, confirmados),
    }


@bp.get("/<int:pid>/estadisticas")
@requiere_admin
def ver_planilla(pid):
    partido = partido_o_404(pid)
    exigir_cerrado(partido)
    return jsonify(planilla(partido))


@bp.put("/<int:pid>/estadisticas")
@requiere_admin
def guardar_planilla(pid):
    """El admin apunta goles, gpp y asistencias de todos a la vez:
    {"jugadores": [{"id": 3, "goles": 2, "gpp": 0, "asistencias": 1}, ...]}

    La planilla es la versión definitiva del partido: sustituye a todo lo apuntado
    antes (incluidos los reportes pendientes de los jugadores; la app los muestra
    ya sumados en la planilla para que el admin los tenga en cuenta).
    Los jugadores que no aparezcan cuentan como 0. Si faltan goles respecto al resultado
    se guarda igualmente y se devuelven avisos; si sobran, se rechaza."""
    partido = partido_o_404(pid)
    exigir_cerrado(partido)
    filas = cuerpo_json().get("jugadores")
    if not isinstance(filas, list) or not all(isinstance(f, dict) for f in filas):
        raise ErrorApi(400, "'jugadores' debe ser una lista")

    convocados = {mp.user_id for mp in partido.titulares}  # los reservas no jugaron
    datos = {}
    for fila in filas:
        uid = fila.get("id")
        if isinstance(uid, bool) or uid not in convocados or uid in datos:
            raise ErrorApi(400, "Cada jugador de la planilla debe ser un jugador distinto de este partido")
        datos[uid] = leer_stats(fila)

    # Que falten goles se permite (avisos); que sobren respecto al resultado, no
    error = exceso_marcador(partido, datos)
    if error:
        raise ErrorApi(400, error)

    StatReport.query.filter_by(match_id=partido.id).delete(synchronize_session=False)
    for uid, valores in datos.items():
        if any(valores.values()):
            db.session.add(StatReport(match_id=partido.id, user_id=uid, estado=REPORTE_CONFIRMADO, **valores))
    db.session.commit()
    return jsonify(planilla(partido))


# ------------------------------------------------------------ después del partido (jugadores)
@bp.post("/<int:pid>/reportes")
@requiere_aprobado
def reportar(pid):
    """Uno de los que jugaron apunta sus goles y gpp; queda pendiente del admin."""
    partido = partido_o_404(pid)
    if not juega(partido, g.usuario.id):
        raise ErrorApi(403, "Solo los que jugaron pueden apuntar goles en este partido")
    exigir_cerrado(partido)
    valores = leer_stats(cuerpo_json())
    if not any(valores.values()):
        raise ErrorApi(400, "Apunta al menos un gol o un gpp")
    if exceso_marcador(partido, con_reporte(stats_confirmadas_del_partido(partido), g.usuario.id, valores)):
        raise ErrorApi(400, "Con eso habría más goles que en el resultado del partido. Revisa lo que apuntas")
    ya = StatReport.query.filter(
        StatReport.match_id == partido.id,
        StatReport.user_id == g.usuario.id,
        StatReport.estado.in_(REPORTES_ACTIVOS),
    ).first()
    if ya:
        raise ErrorApi(409, "Ya tienes datos apuntados en este partido. Si te equivocaste, "
                            "anula el pendiente o díselo al admin")

    r = StatReport(match_id=partido.id, user_id=g.usuario.id, estado=REPORTE_PENDIENTE, **valores)
    db.session.add(r)
    db.session.commit()
    return jsonify(reporte=reporte(r)), 201
