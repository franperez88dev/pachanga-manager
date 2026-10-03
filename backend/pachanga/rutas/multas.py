"""Las multas propias (cada jugador solo ve las suyas; todas, solo el admin en su panel)."""
from flask import Blueprint, g, jsonify

from ..models import Multa
from ..serializadores import multa
from ..seguridad import requiere_aprobado

bp = Blueprint("multas", __name__, url_prefix="/api/multas")


@bp.get("/mias")
@requiere_aprobado
def mias():
    ms = Multa.query.filter_by(user_id=g.usuario.id).order_by(Multa.fecha.desc()).all()
    return jsonify(multas=[multa(m) for m in ms])
