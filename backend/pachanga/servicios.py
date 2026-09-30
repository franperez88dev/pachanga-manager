"""Operaciones con la base de datos que usan varias rutas (y el CLI)."""
import re

from sqlalchemy import func

from .equipos import medias_con_provisional
from .errores import ErrorApi
from .extensions import db
from .models import (
    ESTADO_APROBADO, PARTIDO_CERRADO, REPORTE_CONFIRMADO, ROL_ADMIN,
    Contador, Match, MatchPlayer, Rating, StatReport, User,
)
from .seguridad import normalizar_mote

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


def siguiente_dorsal():
    """Avanza el contador de dorsales. En PostgreSQL, with_for_update bloquea la fila
    para que dos altas simultáneas no se lleven el mismo número."""
    contador = db.session.get(Contador, "dorsal", with_for_update=True)
    if contador is None:
        contador = Contador(nombre="dorsal", valor=0)
        db.session.add(contador)
    contador.valor += 1
    db.session.flush()
    return contador.valor


def crear_usuario(mote, nombre_real=None, rol="jugador", estado="pendiente"):
    mote = validar_mote(mote)
    normalizado = normalizar_mote(mote)
    if User.query.filter_by(mote_normalizado=normalizado).first():
        raise ErrorApi(409, "Ese mote ya está cogido. Prueba con otro")
    usuario = User(
        mote=mote, mote_normalizado=normalizado, nombre_real=validar_nombre_real(nombre_real),
        dorsal=siguiente_dorsal(), rol=rol, estado=estado,
    )
    db.session.add(usuario)
    db.session.flush()
    return usuario


def numero_admins():
    return User.query.filter_by(rol=ROL_ADMIN, estado=ESTADO_APROBADO).count()


def estadisticas(ids=None):
    """{user_id: {"goles", "asistencias", "partidos"}} contando SOLO reportes
    confirmados y partidos cerrados."""
    goles = (
        db.session.query(StatReport.user_id, func.sum(StatReport.goles), func.sum(StatReport.asistencias))
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
        goles = goles.filter(StatReport.user_id.in_(ids))
        partidos = partidos.filter(MatchPlayer.user_id.in_(ids))

    datos = {}
    for uid, g, a in goles:
        datos.setdefault(uid, {"goles": 0, "asistencias": 0, "partidos": 0})
        datos[uid]["goles"] = int(g or 0)
        datos[uid]["asistencias"] = int(a or 0)
    for uid, n in partidos:
        datos.setdefault(uid, {"goles": 0, "asistencias": 0, "partidos": 0})
        datos[uid]["partidos"] = int(n)
    return datos


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
    for convocatoria in MatchPlayer.query.filter_by(user_id=usuario.id).all():
        partido = convocatoria.partido
        db.session.delete(convocatoria)
        if partido.abierto and partido.equipos_generados:
            deshacer_equipos(partido)
    db.session.delete(usuario)
    db.session.commit()


def deshacer_equipos(partido):
    for mp in partido.jugadores:
        mp.equipo = None
    partido.equipos_generados = False
    partido.fuerza_blanco = None
    partido.fuerza_negro = None
