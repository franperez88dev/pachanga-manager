"""Errores de la API: siempre JSON con la forma {"error": "mensaje"}."""
from flask import jsonify
from werkzeug.exceptions import HTTPException


class ErrorApi(Exception):
    def __init__(self, status, mensaje, cabeceras=None):
        super().__init__(mensaje)
        self.status = status
        self.mensaje = mensaje
        self.cabeceras = cabeceras or {}


def registrar_manejadores(app):
    @app.errorhandler(ErrorApi)
    def _error_api(e):
        return jsonify(error=e.mensaje), e.status, e.cabeceras

    @app.errorhandler(HTTPException)
    def _error_http(e):
        mensajes = {404: "No encontrado", 405: "Método no permitido"}
        return jsonify(error=mensajes.get(e.code, e.name)), e.code

    if app.testing:
        return  # en los tests queremos ver la excepción real

    @app.errorhandler(Exception)
    def _error_inesperado(e):
        # Se registra la traza para depurar, pero al cliente no se le da ningún detalle interno
        app.logger.exception("Error no controlado")
        return jsonify(error="Error interno del servidor"), 500
