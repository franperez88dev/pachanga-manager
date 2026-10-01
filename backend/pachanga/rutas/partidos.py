"""Partidos.

Ciclo de vida de un partido:
  1. (admin) Crear -> convocar 10 -> hacer equipos (Rebarajar / Volver a elegir).
  2. (admin) Cerrar indicando el resultado. Desde aquí cuenta como partido jugado.
  3. Goles, gpp y asistencias, por uno de dos caminos (o una mezcla):
     a) El admin rellena la planilla en ese momento: queda todo confirmado.
     b) El admin pulsa "Sig." y cada convocado apunta lo suyo desde su móvil;
        el admin lo confirma o lo descarta cuando pueda.
"""
import random
from datetime import datetime

from flask import Blueprint, current_app, g, jsonify

from ..equipos import JUGADORES_POR_PARTIDO, elegir_reparto
from ..errores import ErrorApi
from ..extensions import db
from ..models import (
    EQUIPO_BLANCO, EQUIPO_NEGRO, PARTIDO_ABIERTO, PARTIDO_CERRADO, REPORTE_CONFIRMADO,
    REPORTE_PENDIENTE, REPORTES_ACTIVOS, Match, MatchPlayer, StatReport, User,
)
from ..serializadores import partido_detalle, partido_resumen, reporte, usuario_publico
from ..seguridad import requiere_admin, requiere_aprobado
from ..servicios import avisos_marcador, deshacer_equipos, fuerzas_de
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


def leer_fecha_y_lugar(datos, parcial=False):
    """Valida 'fecha' (formato 2026-10-04T19:00) y 'lugar'. Con parcial=True son opcionales."""
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
    return cambios


def leer_resultado(partido):
    datos = cuerpo_json()
    partido.goles_blanco = entero(datos, "goles_blanco", 0, MAX_GOLES_EQUIPO)
    partido.goles_negro = entero(datos, "goles_negro", 0, MAX_GOLES_EQUIPO)


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


# ------------------------------------------------------------ antes del partido (admin)
@bp.post("")
@requiere_admin
def crear():
    partido = Match(**leer_fecha_y_lugar(cuerpo_json()))
    db.session.add(partido)
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario)), 201


@bp.patch("/<int:pid>")
@requiere_admin
def editar(pid):
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    for campo, valor in leer_fecha_y_lugar(cuerpo_json(), parcial=True).items():
        setattr(partido, campo, valor)
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


@bp.delete("/<int:pid>")
@requiere_admin
def borrar(pid):
    partido = partido_o_404(pid)
    exigir_abierto(partido)  # un partido abierto aún no tiene goles apuntados
    db.session.delete(partido)
    db.session.commit()
    return "", 204


@bp.put("/<int:pid>/convocatoria")
@requiere_admin
def convocatoria(pid):
    """Recibe {"jugadores": [ids]} con EXACTAMENTE 10 jugadores aprobados distintos.
    Cambiar la convocatoria deshace los equipos que hubiera."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    ids = cuerpo_json().get("jugadores")
    if not isinstance(ids, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ids):
        raise ErrorApi(400, "'jugadores' debe ser una lista de ids")
    if len(set(ids)) != len(ids) or len(ids) != JUGADORES_POR_PARTIDO:
        raise ErrorApi(400, f"La convocatoria debe tener exactamente {JUGADORES_POR_PARTIDO} jugadores distintos")
    usuarios = User.query.filter(User.id.in_(ids)).all()
    if len(usuarios) != len(ids) or not all(u.aprobado for u in usuarios):
        raise ErrorApi(400, "Todos los convocados deben ser jugadores aprobados")

    partido.jugadores.clear()
    db.session.flush()
    partido.jugadores.extend(MatchPlayer(user_id=uid) for uid in ids)
    deshacer_equipos(partido)
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


@bp.post("/<int:pid>/equipos")
@requiere_admin
def crear_equipos(pid):
    """{"rebarajar": false} -> el reparto más igualado ("Crear equipos").
    {"rebarajar": true}  -> otro reparto equilibrado distinto del actual."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    if len(partido.jugadores) != JUGADORES_POR_PARTIDO:
        raise ErrorApi(409, f"Primero convoca a {JUGADORES_POR_PARTIDO} jugadores")

    anterior = None
    if cuerpo_json().get("rebarajar") is True and partido.equipos_generados:
        anterior = (
            {mp.user_id for mp in partido.jugadores if mp.equipo == EQUIPO_BLANCO},
            {mp.user_id for mp in partido.jugadores if mp.equipo == EQUIPO_NEGRO},
        )

    fuerzas = fuerzas_de([mp.user_id for mp in partido.jugadores])
    blanco, _negro, f_blanco, f_negro = elegir_reparto(
        fuerzas, anterior=anterior, tolerancia=current_app.config["TOLERANCIA_REBARAJAR"]
    )
    for mp in partido.jugadores:
        mp.equipo = EQUIPO_BLANCO if mp.user_id in blanco else EQUIPO_NEGRO
    # Quién va de portero, defensa o delantero se sortea (posiciones 0 a 4 en cada equipo)
    azar = random.SystemRandom()
    for color in (EQUIPO_BLANCO, EQUIPO_NEGRO):
        suyos = [mp for mp in partido.jugadores if mp.equipo == color]
        for posicion, mp in enumerate(azar.sample(suyos, len(suyos))):
            mp.posicion = posicion
    partido.equipos_generados = True
    partido.fuerza_blanco = f_blanco
    partido.fuerza_negro = f_negro
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


@bp.delete("/<int:pid>/equipos")
@requiere_admin
def quitar_equipos(pid):
    """Botón "Volver a elegir": se deshacen los equipos y se mantiene la convocatoria."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    deshacer_equipos(partido)
    db.session.commit()
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
    """Estado de los goles de cada convocado: lo confirmado y lo que tenga pendiente."""
    reportes = StatReport.query.filter(
        StatReport.match_id == partido.id, StatReport.estado.in_(REPORTES_ACTIVOS)).all()
    confirmados, pendientes = {}, {}
    for r in reportes:
        destino = confirmados if r.estado == REPORTE_CONFIRMADO else pendientes
        fila = destino.setdefault(r.user_id, {c: 0 for c in CAMPOS_STATS})
        for c in CAMPOS_STATS:
            fila[c] += getattr(r, c)

    cero = {c: 0 for c in CAMPOS_STATS}
    orden = sorted(partido.jugadores, key=lambda mp: (mp.equipo != EQUIPO_BLANCO, mp.usuario.mote.casefold()))
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
    Los convocados que no aparezcan cuentan como 0. Si no cuadra con el resultado,
    se guarda igualmente y se devuelven avisos."""
    partido = partido_o_404(pid)
    exigir_cerrado(partido)
    filas = cuerpo_json().get("jugadores")
    if not isinstance(filas, list) or not all(isinstance(f, dict) for f in filas):
        raise ErrorApi(400, "'jugadores' debe ser una lista")

    convocados = {mp.user_id for mp in partido.jugadores}
    datos = {}
    for fila in filas:
        uid = fila.get("id")
        if isinstance(uid, bool) or uid not in convocados or uid in datos:
            raise ErrorApi(400, "Cada jugador de la planilla debe ser un convocado distinto")
        datos[uid] = leer_stats(fila)

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
    """Un convocado apunta sus goles, gpp y asistencias; queda pendiente del admin."""
    partido = partido_o_404(pid)
    if not any(mp.user_id == g.usuario.id for mp in partido.jugadores):
        raise ErrorApi(403, "Solo los convocados pueden apuntar goles en este partido")
    exigir_cerrado(partido)
    valores = leer_stats(cuerpo_json())
    if not any(valores.values()):
        raise ErrorApi(400, "Apunta al menos un gol o un gpp")
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
