"""Los reportes de goles y asistencias propios."""
from flask import Blueprint, g, jsonify

from ..errores import ErrorApi
from ..extensions import db
from ..models import REPORTE_ANULADO, REPORTE_PENDIENTE, StatReport
from ..serializadores import reporte
from ..seguridad import requiere_aprobado

bp = Blueprint("reportes", __name__, url_prefix="/api/reportes")


@bp.get("/mios")
@requiere_aprobado
def mios():
    rs = StatReport.query.filter_by(user_id=g.usuario.id).order_by(StatReport.fecha.desc()).all()
    return jsonify(reportes=[reporte(r) for r in rs])


@bp.post("/<int:rid>/anular")
@requiere_aprobado
def anular(rid):
    r = db.session.get(StatReport, rid)
    # Si no es tuyo, respondemos 404: ni siquiera confirmamos que exista
    if r is None or r.user_id != g.usuario.id:
        raise ErrorApi(404, "Reporte no encontrado")
    if r.estado != REPORTE_PENDIENTE:
        raise ErrorApi(409, "Solo se puede anular un reporte pendiente")
    r.estado = REPORTE_ANULADO
    db.session.commit()
    return jsonify(reporte=reporte(r))
