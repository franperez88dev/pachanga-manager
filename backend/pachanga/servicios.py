"""Operaciones con la base de datos que usan varias rutas (y el CLI)."""
import re

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from .avatares import persona_aleatoria, validar_avatar
from .equipos import medias_con_provisional
from .errores import ErrorApi
from .extensions import db
from .models import (
    EQUIPO_BLANCO, EQUIPO_NEGRO, ESTADO_APROBADO, PARTIDO_CERRADO, REPORTE_CONFIRMADO,
    ROL_ADMIN, Match, MatchPlayer, Rating, StatReport, User, VotoRebarajar,
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
        .filter(Match.estado == PARTIDO_CERRADO)
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


def avisos_marcador(partido, filas):
    """Avisos (no bloquean) si los goles apuntados no cuadran con el resultado.

    `filas`: {user_id: {"goles", "gpp", "asistencias"}} de los convocados.
    Un gpp de un jugador del Blanco suma un gol al Negro, y al revés.
    """
    equipo_de = {mp.user_id: mp.equipo for mp in partido.jugadores}
    rival = {EQUIPO_BLANCO: EQUIPO_NEGRO, EQUIPO_NEGRO: EQUIPO_BLANCO}
    nombres = {EQUIPO_BLANCO: "el Blanco", EQUIPO_NEGRO: "el Negro"}
    marcador = {EQUIPO_BLANCO: partido.goles_blanco, EQUIPO_NEGRO: partido.goles_negro}

    goles_jugadores = {EQUIPO_BLANCO: 0, EQUIPO_NEGRO: 0}
    goles_en_marcador = {EQUIPO_BLANCO: 0, EQUIPO_NEGRO: 0}
    asistencias = {EQUIPO_BLANCO: 0, EQUIPO_NEGRO: 0}
    for uid, fila in filas.items():
        equipo = equipo_de.get(uid)
        if equipo not in rival:
            continue
        goles_jugadores[equipo] += fila.get("goles", 0)
        goles_en_marcador[equipo] += fila.get("goles", 0)
        goles_en_marcador[rival[equipo]] += fila.get("gpp", 0)
        asistencias[equipo] += fila.get("asistencias", 0)

    avisos = []
    for equipo in (EQUIPO_BLANCO, EQUIPO_NEGRO):
        if marcador[equipo] is not None and goles_en_marcador[equipo] != marcador[equipo]:
            avisos.append(f"Los goles de {nombres[equipo]} suman {goles_en_marcador[equipo]} "
                          f"(contando gpp del rival), pero el resultado dice {marcador[equipo]}")
        if asistencias[equipo] > goles_jugadores[equipo]:
            avisos.append(f"{nombres[equipo].capitalize()} tiene más asistencias "
                          f"({asistencias[equipo]}) que goles de sus jugadores ({goles_jugadores[equipo]})")
    return avisos


def fuerzas_de(ids):
    """Media de estrellas de cada jugador de `ids`. SOLO se usa dentro del backend
    para hacer equipos; nunca sale en ninguna respuesta de la API."""
    medias = dict(
        db.session.query(Rating.rated_id, func.avg(Rating.stars)).group_by(Rating.rated_id).all()
    )
    medias = {uid: float(m) for uid, m in medias.items()}
    return medias_con_provisional(medias, ids)


def borrar_usuario(usuario):
    """Borra la cuenta y todos sus datos: valoraciones dadas y recibidas, reportes
    y convocatorias. Si estaba convocado en un partido abierto con equipos hechos,
    esos equipos se deshacen porque ya no son válidos."""
    if usuario.es_admin and usuario.aprobado and numero_admins() <= 1:
        raise ErrorApi(409, "Eres el único admin. Nombra a otro admin antes de borrar tu cuenta")

    Rating.query.filter(db.or_(Rating.rater_id == usuario.id, Rating.rated_id == usuario.id)).delete(
        synchronize_session=False
    )
    StatReport.query.filter_by(user_id=usuario.id).delete(synchronize_session=False)
    VotoRebarajar.query.filter_by(user_id=usuario.id).delete(synchronize_session=False)
    for convocatoria in MatchPlayer.query.filter_by(user_id=usuario.id).all():
        partido = convocatoria.partido
        db.session.delete(convocatoria)
        if partido.abierto and partido.equipos_generados:
            deshacer_equipos(partido)
    db.session.delete(usuario)
    db.session.commit()


def deshacer_equipos(partido):
    """Se usa cuando cambia la convocatoria: equipos, votos y cuenta de repartos empiezan de cero."""
    for mp in partido.jugadores:
        mp.equipo = None
        mp.posicion = None
        mp.orden_porteria = None
    VotoRebarajar.query.filter_by(match_id=partido.id).delete(synchronize_session=False)
    partido.num_repartos = 0
    partido.equipos_generados = False
    partido.fuerza_blanco = None
    partido.fuerza_negro = None
