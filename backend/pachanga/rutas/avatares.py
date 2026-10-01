"""Catálogo de avatares."""
from flask import Blueprint, jsonify

from ..avatares import BARBAS, COLORES_PELO, ESPECIALES, PEINADOS, PIELES

bp = Blueprint("avatares", __name__)


@bp.get("/api/avatares")
def catalogo():
    """Opciones para el editor de avatar. Es público: se usa en el registro, antes de tener sesión."""
    return jsonify(
        pieles=PIELES,
        colores_pelo=COLORES_PELO,
        peinados=PEINADOS,
        barbas=BARBAS,
        especiales=[{"id": k, "nombre": v} for k, v in ESPECIALES.items()],
    )
