from flask import request

from ..errores import ErrorApi


def cuerpo_json():
    """El cuerpo de la petición como diccionario (o 400 si no es JSON válido)."""
    datos = request.get_json(silent=True)
    if datos is None:
        return {}
    if not isinstance(datos, dict):
        raise ErrorApi(400, "El cuerpo de la petición debe ser un objeto JSON")
    return datos


def entero(datos, campo, minimo, maximo):
    valor = datos.get(campo)
    if isinstance(valor, bool) or not isinstance(valor, int) or not minimo <= valor <= maximo:
        raise ErrorApi(400, f"'{campo}' debe ser un número entero entre {minimo} y {maximo}")
    return valor


def registrar_blueprints(app):
    from . import admin, auth, avatares, cuenta_web, jugadores, partidos, reportes, salud, valoraciones

    for modulo in (salud, auth, cuenta_web, avatares, jugadores, valoraciones, partidos, reportes, admin):
        app.register_blueprint(modulo.bp)
