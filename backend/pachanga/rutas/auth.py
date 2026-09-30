"""Registro, login y la cuenta propia."""
from flask import Blueprint, current_app, g, jsonify, request

from ..errores import ErrorApi
from ..extensions import db
from ..serializadores import usuario_propio
from ..seguridad import (
    clave_intento, crear_token, error_demasiados_intentos, requiere_sesion,
    segundos_bloqueado, sumar_intento, verificar_credenciales,
)
from ..servicios import borrar_usuario, crear_usuario
from . import cuerpo_json

bp = Blueprint("auth", __name__, url_prefix="/api")


@bp.post("/auth/registro")
def registro():
    datos = cuerpo_json()
    # Límite de altas por IP para que nadie llene la lista de pendientes con basura
    clave_ip = clave_intento("registro-ip", request.remote_addr or "desconocida")
    espera = segundos_bloqueado(clave_ip)
    if espera:
        raise error_demasiados_intentos(espera)

    usuario, pin = crear_usuario(datos.get("mote"), datos.get("nombre_real"))
    sumar_intento(clave_ip, current_app.config["REGISTRO_MAX_POR_IP_HORA"], 60)
    db.session.commit()
    # Única vez que el jugador recibe su PIN: la app se lo enseña en grande para que lo apunte
    return jsonify(pin=pin, token=crear_token(usuario), usuario=usuario_propio(usuario)), 201


@bp.post("/auth/login")
def login():
    datos = cuerpo_json()
    mote, pin = str(datos.get("mote") or ""), str(datos.get("pin") or "")
    if not mote.strip() or not pin.strip():
        raise ErrorApi(400, "Escribe tu mote y tu PIN")
    usuario = verificar_credenciales(mote, pin)
    return jsonify(token=crear_token(usuario), usuario=usuario_propio(usuario))


@bp.get("/yo")
@requiere_sesion
def yo():
    """La app lo consulta al arrancar para saber quién eres, tu rol y si ya te aprobaron."""
    return jsonify(usuario=usuario_propio(g.usuario))


@bp.delete("/yo")
@requiere_sesion
def borrar_mi_cuenta():
    if cuerpo_json().get("confirmar") is not True:
        raise ErrorApi(400, "Falta confirmar el borrado")
    borrar_usuario(g.usuario)
    return "", 204
