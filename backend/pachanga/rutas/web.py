"""Sirve la app web ya compilada (la carpeta pachanga/web, que genera `npm run build` en app/).

La app de React y la API viven en el mismo servidor y dominio:
  /               -> index.html (la app)
  /assets/...     -> JavaScript, estilos, fuentes e imágenes compilados
  /favicon.svg, /manifest.webmanifest, /tema.js...  -> archivos sueltos de app/public
  /api/...        -> la API (el resto de blueprints)
"""
import os

from flask import Blueprint, current_app, send_from_directory
from werkzeug.exceptions import NotFound

bp = Blueprint("web", __name__)

# Solo se sirven archivos sueltos con estas extensiones (nada de .py, .env, etc.)
# (.js: solo tema.js, que tiene que cargarse antes que la app para no dar un fogonazo de color)
EXTENSIONES_PERMITIDAS = {".svg", ".png", ".ico", ".webmanifest", ".txt", ".js"}

# Política de seguridad del navegador para la página: solo carga cosas de nuestro propio servidor.
# 'unsafe-inline' en estilos hace falta porque React pone estilos en línea (style={{...}}).
CSP = ("default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
       "base-uri 'self'; form-action 'self'; frame-ancestors 'none'")

AVISO_SIN_COMPILAR = (
    "La app web todavia no esta compilada.\n"
    "En tu PC: abre una terminal en la carpeta app y ejecuta  npm run build\n"
    "(eso crea backend/pachanga/web). Mientras desarrollas, usa  npm run dev  (puerto 5173).\n"
)


def carpeta_web():
    return current_app.config["CARPETA_WEB"]


@bp.get("/")
def inicio():
    if not os.path.isfile(os.path.join(carpeta_web(), "index.html")):
        return AVISO_SIN_COMPILAR, 503, {"Content-Type": "text/plain; charset=utf-8"}
    respuesta = send_from_directory(carpeta_web(), "index.html")
    # El index NO se guarda en caché: así, tras actualizar, todos reciben la versión nueva al abrir
    respuesta.headers["Cache-Control"] = "no-cache"
    respuesta.headers["Content-Security-Policy"] = CSP
    respuesta.headers["X-Frame-Options"] = "DENY"
    return respuesta


@bp.get("/assets/<path:archivo>")
def assets(archivo):
    # Los nombres llevan un código que cambia en cada compilación (index-a1b2c3.js),
    # así que el navegador puede guardarlos "para siempre"
    respuesta = send_from_directory(os.path.join(carpeta_web(), "assets"), archivo, max_age=31536000)
    respuesta.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return respuesta


@bp.get("/<archivo>")
def archivo_suelto(archivo):
    """favicon.svg, manifest.webmanifest, iconos... (lo que hay en app/public)."""
    if os.path.splitext(archivo)[1].lower() not in EXTENSIONES_PERMITIDAS:
        raise NotFound()
    return send_from_directory(carpeta_web(), archivo, max_age=3600)
