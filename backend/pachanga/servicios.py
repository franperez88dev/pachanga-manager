"""Operaciones con la base de datos que usan varias rutas (y el CLI)."""
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import current_app
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from .avatares import persona_aleatoria, validar_avatar
from .equipos import medias_con_provisional
from .errores import ErrorApi
from .extensions import db
from .models import (
    EQUIPO_BLANCO, EQUIPO_NEGRO, ESTADO_APROBADO, PARTIDO_CERRADO, REPORTE_CONFIRMADO,
    ROL_ADMIN, Match, MatchPlayer, Multa, Rating, StatReport, User, VotoRebarajar,
)
from .seguridad import hash_pin, normalizar_mote, nuevo_pin

# Letras (con tildes y ñ), números, espacios, punto, guion y apóstrofo
_PATRON_MOTE = re.compile(r"^[\w .'-]{2,20}$")


def validar_mote(mote):
    mote = " ".join(str(mote or "").split())
    if not _PATRON_MOTE.match(mote) or "_" in mote:
        raise ErrorApi(400, "El mote debe tener entre 2 y 20 caracteres (letras, números, espacios, . ' -)")
    return mote


def validar_nombre_real(nombre):
    nombre = " ".join(str(nombre or "").split())
    if len(nombre) > 60:
        raise ErrorApi(400, "El nombre real no puede pasar de 60 caracteres")
    return nombre or None


def dorsal_libre():
    """El dorsal libre más bajo. Si se borra la cuenta del 04, el siguiente que llegue se lo queda."""
    ocupados = {d for (d,) in db.session.query(User.dorsal)}
    dorsal = 1
    while dorsal in ocupados:
        dorsal += 1
    return dorsal


def _mote_cogido(normalizado):
    return User.query.filter_by(mote_normalizado=normalizado).first() is not None


def crear_usuario(mote, nombre_real=None, rol="jugador", estado="pendiente", avatar=None):
    """Crea el usuario con el dorsal libre más bajo y un PIN nuevo. Sin avatar, le toca uno al azar.
    Devuelve (usuario, pin): el PIN en claro solo existe en este momento."""
    mote = validar_mote(mote)
    normalizado = normalizar_mote(mote)
    nombre_real = validar_nombre_real(nombre_real)
    avatar = validar_avatar(avatar) if avatar is not None else persona_aleatoria()
    if _mote_cogido(normalizado):
        raise ErrorApi(409, "Ese mote ya está cogido. Prueba con otro")

    pin = nuevo_pin()
    # Si dos personas se registran a la vez, las dos pueden calcular el mismo dorsal libre:
    # la restricción UNIQUE salta en la segunda, y esta reintenta con el siguiente.
    for _ in range(5):
        usuario = User(mote=mote, mote_normalizado=normalizado, nombre_real=nombre_real,
                       dorsal=dorsal_libre(), pin_hash=hash_pin(pin), rol=rol, estado=estado, avatar=avatar)
        try:
            with db.session.begin_nested():  # "punto de guardado": si falla, solo se deshace esto
                db.session.add(usuario)
        except IntegrityError:
            if _mote_cogido(normalizado):
                raise ErrorApi(409, "Ese mote ya está cogido. Prueba con otro")
            continue
        return usuario, pin
    raise ErrorApi(409, "Hay mucha gente registrándose a la vez. Vuelve a intentarlo")


def regenerar_pin(usuario):
    """PIN nuevo (para quien lo olvidó). Cierra sus sesiones abiertas en otros móviles."""
    pin = nuevo_pin()
    usuario.pin_hash = hash_pin(pin)
    usuario.version_token += 1
    return pin


def numero_admins():
    return User.query.filter_by(rol=ROL_ADMIN, estado=ESTADO_APROBADO).count()


def stats_a_cero():
    return {"goles": 0, "asistencias": 0, "gpp": 0, "partidos": 0}


def estadisticas(ids=None):
    """{user_id: {"goles", "asistencias", "gpp", "partidos"}} contando SOLO reportes
    confirmados y partidos cerrados."""
    sumas = (
        db.session.query(StatReport.user_id, func.sum(StatReport.goles),
                         func.sum(StatReport.asistencias), func.sum(StatReport.gpp))
        .join(Match, Match.id == StatReport.match_id)
        .filter(StatReport.estado == REPORTE_CONFIRMADO, Match.estado == PARTIDO_CERRADO)
        .group_by(StatReport.user_id)
    )
    partidos = (
        db.session.query(MatchPlayer.user_id, func.count(MatchPlayer.match_id))
        .join(Match, Match.id == MatchPlayer.match_id)
        .filter(Match.estado == PARTIDO_CERRADO, MatchPlayer.equipo.isnot(None))  # los reservas no jugaron
        .group_by(MatchPlayer.user_id)
    )
    if ids is not None:
        sumas = sumas.filter(StatReport.user_id.in_(ids))
        partidos = partidos.filter(MatchPlayer.user_id.in_(ids))

    datos = {}
    for uid, g, a, p in sumas:
        fila = datos.setdefault(uid, stats_a_cero())
        fila.update(goles=int(g or 0), asistencias=int(a or 0), gpp=int(p or 0))
    for uid, n in partidos:
        datos.setdefault(uid, stats_a_cero())["partidos"] = int(n)
    return datos


NOMBRE_EQUIPO = {EQUIPO_BLANCO: "Nevados C.F.", EQUIPO_NEGRO: "Sombras F.C."}
_RIVAL = {EQUIPO_BLANCO: EQUIPO_NEGRO, EQUIPO_NEGRO: EQUIPO_BLANCO}


def _sumas_por_equipo(partido, filas):
    """Suma lo apuntado en `filas` ({user_id: {"goles", "gpp", "asistencias"}}) por equipo.
    Un gpp de un jugador del Blanco suma un gol al Negro, y al revés."""
    equipo_de = {mp.user_id: mp.equipo for mp in partido.jugadores}
    en_marcador = {EQUIPO_BLANCO: 0, EQUIPO_NEGRO: 0}  # goles que cuentan en el resultado
    de_jugadores = {EQUIPO_BLANCO: 0, EQUIPO_NEGRO: 0}  # goles marcados por sus jugadores
    asistencias = {EQUIPO_BLANCO: 0, EQUIPO_NEGRO: 0}
    for uid, fila in filas.items():
        equipo = equipo_de.get(uid)
        if equipo not in _RIVAL:
            continue
        en_marcador[equipo] += fila.get("goles", 0)
        en_marcador[_RIVAL[equipo]] += fila.get("gpp", 0)
        de_jugadores[equipo] += fila.get("goles", 0)
        asistencias[equipo] += fila.get("asistencias", 0)
    return en_marcador, de_jugadores, asistencias


def marcador_de(partido):
    return {EQUIPO_BLANCO: partido.goles_blanco, EQUIPO_NEGRO: partido.goles_negro}


def exceso_marcador(partido, filas):
    """Mensaje de error si algún equipo tendría MÁS goles que el resultado; None si no.
    Que falten goles está permitido (se pueden apuntar más tarde); que sobren, no."""
    en_marcador, _, _ = _sumas_por_equipo(partido, filas)
    for equipo, resultado in marcador_de(partido).items():
        if resultado is not None and en_marcador[equipo] > resultado:
            return (f"{NOMBRE_EQUIPO[equipo]} tendría {en_marcador[equipo]} goles (contando los gpp del rival) "
                    f"y el resultado es {resultado}. No puede haber más goles que en el resultado.")
    return None


def avisos_marcador(partido, filas):
    """Avisos que NO bloquean: faltan goles por apuntar, o más asistencias que goles."""
    en_marcador, de_jugadores, asistencias = _sumas_por_equipo(partido, filas)
    avisos = []
    for equipo, resultado in marcador_de(partido).items():
        if resultado is not None and en_marcador[equipo] < resultado:
            avisos.append(f"Faltan goles de {NOMBRE_EQUIPO[equipo]}: hay {en_marcador[equipo]} apuntados "
                          f"(contando gpp del rival) y el resultado es {resultado}")
        if asistencias[equipo] > de_jugadores[equipo]:
            avisos.append(f"{NOMBRE_EQUIPO[equipo]} tiene más asistencias "
                          f"({asistencias[equipo]}) que goles de sus jugadores ({de_jugadores[equipo]})")
    return avisos


def stats_confirmadas_del_partido(partido):
    """{user_id: {"goles", "gpp", "asistencias"}} con lo YA confirmado en este partido."""
    filas = {}
    for r in StatReport.query.filter_by(match_id=partido.id, estado=REPORTE_CONFIRMADO):
        fila = filas.setdefault(r.user_id, {"goles": 0, "gpp": 0, "asistencias": 0})
        fila["goles"] += r.goles
        fila["gpp"] += r.gpp
        fila["asistencias"] += r.asistencias
    return filas


def con_reporte(filas, reporte_usuario, valores):
    """Copia de `filas` sumando los `valores` de un reporte más (para comprobar antes de guardar)."""
    resultado = {uid: dict(v) for uid, v in filas.items()}
    fila = resultado.setdefault(reporte_usuario, {"goles": 0, "gpp": 0, "asistencias": 0})
    for campo in ("goles", "gpp", "asistencias"):
        fila[campo] += valores.get(campo, 0)
    return resultado


def fuerzas_de(ids):
    """Media de estrellas de cada jugador de `ids`. SOLO se usa dentro del backend
    para hacer equipos; nunca sale en ninguna respuesta de la API."""
    medias = dict(
        db.session.query(Rating.rated_id, func.avg(Rating.stars)).group_by(Rating.rated_id).all()
    )
    medias = {uid: float(m) for uid, m in medias.items()}
    return medias_con_provisional(medias, ids)


def borrar_usuario(usuario):
    """Borra la cuenta y todos sus datos: valoraciones dadas y recibidas, goles, multas, votos
    y huecos reservados. Si jugaba en un partido abierto con los equipos hechos, esos equipos
    se deshacen porque ya no son válidos."""
    if usuario.es_admin and usuario.aprobado and numero_admins() <= 1:
        raise ErrorApi(409, "Eres el único admin. Nombra a otro admin antes de borrar tu cuenta")

    Rating.query.filter(db.or_(Rating.rater_id == usuario.id, Rating.rated_id == usuario.id)).delete(
        synchronize_session=False
    )
    StatReport.query.filter_by(user_id=usuario.id).delete(synchronize_session=False)
    VotoRebarajar.query.filter_by(user_id=usuario.id).delete(synchronize_session=False)
    Multa.query.filter_by(user_id=usuario.id).delete(synchronize_session=False)
    for plaza in MatchPlayer.query.filter_by(user_id=usuario.id).all():
        partido = plaza.partido
        jugaba = plaza.equipo is not None
        partido.jugadores.remove(plaza)
        if partido.abierto and partido.equipos_generados and jugaba:
            deshacer_equipos(partido)
    db.session.delete(usuario)
    db.session.commit()


# ------------------------------------------------------------ horarios y multas
def ahora_local():
    """La hora actual en España, sin zona: en el mismo formato en que se guarda la fecha de los
    partidos. (El servidor de PythonAnywhere va en hora UTC, una o dos horas menos.)"""
    return datetime.now(ZoneInfo(current_app.config["ZONA_HORARIA"])).replace(tzinfo=None)


def horas_para_empezar(partido):
    return (partido.fecha - ahora_local()).total_seconds() / 3600


def lleva_multa(partido):
    """¿Borrarse AHORA de este partido lleva multa? Sí, si faltan menos de 24 horas."""
    return horas_para_empezar(partido) < current_app.config["HORAS_SIN_MULTA"]


def poner_multa(partido, usuario_id, motivo):
    multa = Multa(match_id=partido.id, user_id=usuario_id, motivo=motivo)
    db.session.add(multa)
    return multa


def deshacer_equipos(partido):
    """Se usa cuando cambia quién juega: equipos, votos y cuenta de repartos empiezan de cero."""
    for mp in partido.jugadores:
        mp.equipo = None
        mp.posicion = None
        mp.orden_porteria = None
    VotoRebarajar.query.filter_by(match_id=partido.id).delete(synchronize_session=False)
    partido.num_repartos = 0
    partido.equipos_generados = False
    partido.fuerza_blanco = None
    partido.fuerza_negro = None
