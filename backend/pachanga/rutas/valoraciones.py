"""Valoraciones secretas: se envían una vez y no se pueden ver ni editar.

La API solo dice A QUIÉN has valorado ya, nunca cuántas estrellas (ni tuyas ni de nadie).
"""
from flask import Blueprint, g, jsonify
from sqlalchemy.exc import IntegrityError

from ..errores import ErrorApi
from ..extensions import db
from ..models import Rating, User
from ..seguridad import requiere_aprobado
from . import cuerpo_json, entero

bp = Blueprint("valoraciones", __name__, url_prefix="/api/valoraciones")


@bp.get("/mias")
@requiere_aprobado
def mias():
    ids = [r.rated_id for r in Rating.query.filter_by(rater_id=g.usuario.id).all()]
    return jsonify(valorados=ids)


@bp.post("")
@requiere_aprobado
def valorar():
    datos = cuerpo_json()
    valorado_id = entero(datos, "valorado_id", 1, 2**31 - 1)
    estrellas = entero(datos, "estrellas", 1, 5)

    if valorado_id == g.usuario.id:
        raise ErrorApi(400, "No puedes valorarte a ti mismo")
    valorado = db.session.get(User, valorado_id)
    if valorado is None or not valorado.aprobado:
        raise ErrorApi(404, "Jugador no encontrado")
    if Rating.query.filter_by(rater_id=g.usuario.id, rated_id=valorado_id).first():
        raise ErrorApi(409, "Ya valoraste a este jugador y no se puede cambiar")

    db.session.add(Rating(rater_id=g.usuario.id, rated_id=valorado_id, stars=estrellas))
    try:
        db.session.commit()
    except IntegrityError:
        # Dos envíos casi a la vez: la restricción UNIQUE de la base de datos manda
        db.session.rollback()
        raise ErrorApi(409, "Ya valoraste a este jugador y no se puede cambiar")
    return jsonify(valorado_id=valorado_id), 201
