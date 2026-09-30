"""Panel de admin: altas, admins, confirmar goles y PIN nuevo para quien lo olvide."""
from flask import Blueprint, jsonify, request

from ..errores import ErrorApi
from ..extensions import db
from ..models import (
    ESTADO_APROBADO, ESTADO_PENDIENTE, REPORTE_CONFIRMADO,
    REPORTE_DESCARTADO, REPORTE_PENDIENTE, ROL_ADMIN, ROL_JUGADOR, StatReport, User,
)
from ..serializadores import reporte, usuario_admin
from ..seguridad import requiere_admin
from ..servicios import numero_admins, regenerar_pin
from . import cuerpo_json

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
