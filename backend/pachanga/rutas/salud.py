from flask import Blueprint, jsonify

bp = Blueprint("salud", __name__)


@bp.get("/health")
def health():
    """Comprobación ligera (no toca la base de datos). La app la usa para saber si el
    servidor está despierto y el servicio de ping, para que no se duerma."""
    return jsonify(estado="ok")
