"""Las multas propias (cada jugador solo ve las suyas; todas, solo el admin en su panel)."""
from flask import Blueprint, g, jsonify

from ..errores import ErrorApi
from ..extensions import db
from ..models import MULTA_PENDIENTE, Multa, ahora
from ..serializadores import multa
from ..seguridad import requiere_aprobado

bp = Blueprint("multas", __name__, url_prefix="/api/multas")


@bp.get("/mias")
@requiere_aprobado
def mias():
    ms = Multa.query.filter_by(user_id=g.usuario.id).order_by(Multa.fecha.desc(), Multa.id.desc()).all()
    return jsonify(multas=[multa(m) for m in ms])


def mi_multa_pendiente(mid):
    m = db.session.get(Multa, mid)
    # Si no es tuya, respondemos 404: ni siquiera confirmamos que exista
    if m is None or m.user_id != g.usuario.id:
        raise ErrorApi(404, "Multa no encontrada")
    if m.estado != MULTA_PENDIENTE:
        raise ErrorApi(409, "Esa multa ya está resuelta")
    return m


@bp.post("/<int:mid>/aviso-pago")
@requiere_aprobado
def avisar_pago(mid):
    """El jugador dice "ya la he pagado". La multa sigue pendiente hasta que el admin lo confirme:
    a él le aparece el aviso en su panel."""
    m = mi_multa_pendiente(mid)
    if m.aviso_pago is None:
        m.aviso_pago = ahora()
        db.session.commit()
    return jsonify(multa=multa(m))


@bp.delete("/<int:mid>/aviso-pago")
@requiere_aprobado
def retirar_aviso_pago(mid):
    """Por si pulsó sin querer."""
    m = mi_multa_pendiente(mid)
    m.aviso_pago = None
    db.session.commit()
    return jsonify(multa=multa(m))
