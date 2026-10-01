"""Catálogo de avatares e imágenes que suben los admins."""
from flask import Blueprint, Response, jsonify, request

from ..avatares import (
    BARBAS, COLORES_PELO, ESPECIALES, MAX_BYTES_IMAGEN, PEINADOS, PIELES, PREFIJO_SUBIDO, tipo_de_imagen,
)
from ..errores import ErrorApi
from ..extensions import db
from ..models import AvatarSubido
from ..seguridad import requiere_admin

bp = Blueprint("avatares", __name__)


def subido_en_catalogo(a):
    return {"id": f"{PREFIJO_SUBIDO}{a.id}", "nombre": a.nombre, "imagen": f"/avatares/{a.id}"}


@bp.get("/api/avatares")
def catalogo():
    """Opciones para el editor de avatar. Es público: se usa en el registro, antes de tener sesión."""
    subidos = AvatarSubido.query.filter_by(activo=True).order_by(AvatarSubido.id).all()
    return jsonify(
        pieles=PIELES,
        colores_pelo=COLORES_PELO,
        peinados=PEINADOS,
        barbas=BARBAS,
        especiales=[{"id": k, "nombre": v} for k, v in ESPECIALES.items()]
        + [subido_en_catalogo(a) for a in subidos],
    )


@bp.get("/avatares/<int:aid>")
def imagen(aid):
    a = db.session.get(AvatarSubido, aid)
    if a is None:  # los desactivados se siguen sirviendo: quien ya lo tenía no lo pierde
        raise ErrorApi(404, "Avatar no encontrado")
    return Response(a.datos, mimetype=a.mime, headers={
        "Cache-Control": "public, max-age=86400",
        "X-Content-Type-Options": "nosniff",  # el navegador no debe "adivinar" otro tipo
        "Content-Security-Policy": "default-src 'none'",
    })


@bp.post("/api/admin/avatares")
@requiere_admin
def subir():
    """Formulario multipart con 'nombre' y 'imagen' (PNG, JPEG o WebP, máx. 300 KB)."""
    nombre = " ".join(request.form.get("nombre", "").split())
    if not 1 <= len(nombre) <= 30:
        raise ErrorApi(400, "Ponle un nombre al avatar (máximo 30 caracteres)")
    fichero = request.files.get("imagen")
    if fichero is None:
        raise ErrorApi(400, "Falta la imagen")
    contenido = fichero.read(MAX_BYTES_IMAGEN + 1)
    if len(contenido) > MAX_BYTES_IMAGEN:
        raise ErrorApi(400, "La imagen pesa demasiado (máximo 300 KB)")
    mime = tipo_de_imagen(contenido)
    if mime is None:
        raise ErrorApi(400, "Formato no válido: usa PNG, JPEG o WebP")

    a = AvatarSubido(nombre=nombre, mime=mime, datos=contenido)
    db.session.add(a)
    db.session.commit()
    return jsonify(avatar=subido_en_catalogo(a)), 201


@bp.delete("/api/admin/avatares/<int:aid>")
@requiere_admin
def retirar(aid):
    """Lo quita del catálogo. Quien ya lo tenga puesto lo conserva."""
    a = db.session.get(AvatarSubido, aid)
    if a is None or not a.activo:
        raise ErrorApi(404, "Avatar no encontrado")
    a.activo = False
    db.session.commit()
    return "", 204
