"""Pachanga Manager: API REST en Flask.

create_app() es una "fábrica": construye la app con su configuración. Los tests
la llaman con una configuración propia (base de datos en memoria).
"""
import os

from flask import Flask, request
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from .cli import registrar_comandos
from .config import cargar_config
from .errores import registrar_manejadores
from .extensions import db
from .rutas import registrar_blueprints


def create_app(config_extra=None):
    app = Flask(__name__)
    app.json.sort_keys = False  # respeta el orden de los campos tal como los escribimos
    app.config.update(cargar_config())
    if config_extra:
        app.config.update(config_extra)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Falta SECRET_KEY. Copia backend/.env.example a backend/.env y rellénalo")

    if app.config["CONFIAR_EN_PROXY"]:
        # Para que request.remote_addr sea la IP del móvil y no la del proxy del hosting
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGENES"]},
                   r"/health": {"origins": app.config["CORS_ORIGENES"]}},
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )

    db.init_app(app)
    registrar_manejadores(app)
    registrar_blueprints(app)
    registrar_comandos(app)

    @app.after_request
    def sin_cache(respuesta):
        # Las respuestas de la API son personales: que nadie (proxy, WebView) las guarde
        if request.path.startswith("/api/"):
            respuesta.headers["Cache-Control"] = "no-store"
        return respuesta

    os.makedirs(app.instance_path, exist_ok=True)
    with app.app_context():
        db.create_all()  # crea las tablas que falten (no modifica las existentes)

    return app
