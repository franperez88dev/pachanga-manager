"""Plantilla, perfiles y clasificación (para cualquier jugador aprobado)."""
from flask import Blueprint, jsonify, request

from ..errores import ErrorApi
from ..extensions import db
from ..models import ESTADO_APROBADO, User
from ..serializadores import usuario_publico
from ..seguridad import requiere_aprobado
from ..servicios import estadisticas

bp = Blueprint("jugadores", __name__, url_prefix="/api")

ORDENES = ("goles", "asistencias", "partidos")
_CERO = {"goles": 0, "asistencias": 0, "partidos": 0}


def aprobados():
    return User.query.filter_by(estado=ESTADO_APROBADO).order_by(db.func.lower(User.mote)).all()


@bp.get("/jugadores")
@requiere_aprobado
def lista():
    return jsonify(jugadores=[usuario_publico(u) for u in aprobados()])


@bp.get("/jugadores/<int:uid>")
@requiere_aprobado
def perfil(uid):
    u = db.session.get(User, uid)
    if u is None or not u.aprobado:
        raise ErrorApi(404, "Jugador no encontrado")
    stats = estadisticas([u.id]).get(u.id, _CERO)
    return jsonify(jugador={**usuario_publico(u), **stats})


@bp.get("/clasificacion")
@requiere_aprobado
def clasificacion():
    orden = request.args.get("orden", "goles")
    if orden not in ORDENES:
        raise ErrorApi(400, f"Orden no válido. Usa uno de: {', '.join(ORDENES)}")
    stats = estadisticas()
    filas = [{**usuario_publico(u), **stats.get(u.id, _CERO)} for u in aprobados()]
    # Desempate: el resto de columnas y, al final, el mote
    otras = [c for c in ORDENES if c != orden]
    filas.sort(key=lambda f: (-f[orden], -f[otras[0]], -f[otras[1]], f["mote"].casefold()))
    return jsonify(orden=orden, clasificacion=filas)
