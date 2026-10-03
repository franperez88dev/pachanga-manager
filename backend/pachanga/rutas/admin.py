"""Panel de admin: altas, admins, confirmar goles, multas y PIN nuevo para quien lo olvide."""
from flask import Blueprint, g, jsonify, request

from ..errores import ErrorApi
from ..extensions import db
from ..models import (
    ESTADO_APROBADO, ESTADO_PENDIENTE, MULTA_PAGADA, MULTA_PENDIENTE, MULTA_PERDONADA, REPORTE_CONFIRMADO,
    REPORTE_DESCARTADO, REPORTE_PENDIENTE, ROL_ADMIN, ROL_JUGADOR, Multa, StatReport, User,
)
from ..serializadores import multa_admin, reporte, usuario_admin
from ..seguridad import requiere_admin
from ..servicios import (
    con_reporte, exceso_marcador, motes_de_admins, numero_admins, regenerar_pin, stats_confirmadas_del_partido,
)
from . import cuerpo_json, entero

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def usuario_o_404(uid):
    u = db.session.get(User, uid)
    if u is None:
        raise ErrorApi(404, "Usuario no encontrado")
    return u


# ------------------------------------------------------------ altas
@bp.get("/altas")
@requiere_admin
def altas_pendientes():
    us = User.query.filter_by(estado=ESTADO_PENDIENTE).order_by(User.fecha_alta).all()
    return jsonify(altas=[usuario_admin(u) for u in us])


def alta_pendiente_o_error(uid):
    u = usuario_o_404(uid)
    if u.estado != ESTADO_PENDIENTE:
        raise ErrorApi(409, "Esa alta ya estaba resuelta")
    return u


@bp.post("/usuarios/<int:uid>/aprobar")
@requiere_admin
def aprobar(uid):
    u = alta_pendiente_o_error(uid)
    u.estado = ESTADO_APROBADO
    db.session.commit()
    return jsonify(usuario=usuario_admin(u))


@bp.post("/usuarios/<int:uid>/rechazar")
@requiere_admin
def rechazar(uid):
    # Un alta rechazada se borra: su mote y su dorsal quedan libres para otro
    u = alta_pendiente_o_error(uid)
    db.session.delete(u)
    db.session.commit()
    return "", 204


# ------------------------------------------------------------ gestión de admins
@bp.get("/usuarios")
@requiere_admin
def usuarios():
    us = User.query.filter_by(estado=ESTADO_APROBADO).order_by(db.func.lower(User.mote)).all()
    return jsonify(usuarios=[usuario_admin(u) for u in us])


@bp.put("/usuarios/<int:uid>/rol")
@requiere_admin
def cambiar_rol(uid):
    rol = cuerpo_json().get("rol")
    if rol not in (ROL_ADMIN, ROL_JUGADOR):
        raise ErrorApi(400, "El rol debe ser 'admin' o 'jugador'")
    u = usuario_o_404(uid)
    if not u.aprobado:
        raise ErrorApi(409, "Solo se puede cambiar el rol de jugadores aprobados")
    if rol == ROL_JUGADOR and u.es_admin and numero_admins() <= 1:
        raise ErrorApi(409, "Tiene que quedar al menos un admin")
    u.rol = rol
    db.session.commit()
    return jsonify(usuario=usuario_admin(u))


# ------------------------------------------------------------ PIN olvidado
@bp.post("/usuarios/<int:uid>/pin")
@requiere_admin
def nuevo_pin_para(uid):
    """El PIN no se puede consultar (solo guardamos su hash). Si alguien lo olvida, el admin
    genera uno nuevo, se lo pasa por WhatsApp y las sesiones antiguas de ese jugador se cierran."""
    u = usuario_o_404(uid)
    pin = regenerar_pin(u)
    db.session.commit()
    return jsonify(id=u.id, mote=u.mote, pin=pin)


# ------------------------------------------------------------ goles por confirmar
@bp.get("/reportes")
@requiere_admin
def reportes():
    estado = request.args.get("estado", REPORTE_PENDIENTE)
    rs = StatReport.query.filter_by(estado=estado).order_by(StatReport.fecha).all()
    return jsonify(reportes=[reporte(r) for r in rs])


def _resolver_reporte(rid, nuevo_estado):
    r = db.session.get(StatReport, rid)
    if r is None:
        raise ErrorApi(404, "Reporte no encontrado")
    if r.estado != REPORTE_PENDIENTE:
        raise ErrorApi(409, "Ese reporte ya no está pendiente")
    if nuevo_estado == REPORTE_CONFIRMADO:
        valores = {"goles": r.goles, "gpp": r.gpp, "asistencias": r.asistencias}
        error = exceso_marcador(r.partido, con_reporte(stats_confirmadas_del_partido(r.partido), r.user_id, valores))
        if error:
            raise ErrorApi(409, f"No se puede confirmar: {error} Descártalo o corrige la planilla.")
    r.estado = nuevo_estado
    db.session.commit()
    return jsonify(reporte=reporte(r))


@bp.post("/reportes/<int:rid>/confirmar")
@requiere_admin
def confirmar(rid):
    return _resolver_reporte(rid, REPORTE_CONFIRMADO)


@bp.post("/reportes/<int:rid>/descartar")
@requiere_admin
def descartar(rid):
    return _resolver_reporte(rid, REPORTE_DESCARTADO)


# ------------------------------------------------------------ multas
MAX_MULTA_CENTIMOS = 10000  # 100 €
PASO_MULTA_CENTIMOS = 10


@bp.get("/multas")
@requiere_admin
def multas():
    """Todas las multas, las más recientes primero (la app las separa en pendientes y resueltas)."""
    ms = Multa.query.order_by(Multa.fecha.desc(), Multa.id.desc()).all()
    admins = motes_de_admins()
    return jsonify(multas=[multa_admin(m, g.usuario, admins) for m in ms])


@bp.put("/multas/<int:mid>")
@requiere_admin
def cambiar_multa(mid):
    """Uno o los dos campos:
    {"estado": "pagada" | "perdonada" | "pendiente"}  ("pendiente" deshace un toque equivocado)
    {"importe_centimos": 30}                          (de 10 en 10 céntimos; solo si está pendiente)"""
    datos = cuerpo_json()
    if "estado" not in datos and "importe_centimos" not in datos:
        raise ErrorApi(400, "Indica 'estado' o 'importe_centimos'")
    m = db.session.get(Multa, mid)
    if m is None:
        raise ErrorApi(404, "Multa no encontrada")

    if "importe_centimos" in datos:
        importe = entero(datos, "importe_centimos", 0, MAX_MULTA_CENTIMOS)
        if importe % PASO_MULTA_CENTIMOS:
            raise ErrorApi(400, f"El importe va de {PASO_MULTA_CENTIMOS} en {PASO_MULTA_CENTIMOS} céntimos")
        if m.estado != MULTA_PENDIENTE:
            raise ErrorApi(409, "Solo se cambia el importe de una multa pendiente")
        m.importe_centimos = importe
    if "estado" in datos:
        if datos["estado"] not in (MULTA_PAGADA, MULTA_PERDONADA, MULTA_PENDIENTE):
            raise ErrorApi(400, "El estado debe ser 'pagada', 'perdonada' o 'pendiente'")
        m.estado = datos["estado"]
        m.aviso_pago = None  # el aviso del jugador ya está atendido (o, al deshacer, se empieza de nuevo)
    db.session.commit()
    return jsonify(multa=multa_admin(m, g.usuario, motes_de_admins()))
