"""Avatares de los jugadores.

Un avatar se guarda como un pequeño JSON en el usuario. Hay dos tipos:

- "persona": un muñeco que el jugador personaliza.
      {"tipo": "persona", "piel": "#e0ac69", "peinado": "tupe", "color_pelo": "#3b2417",
       "barba": "perilla", "color_barba": "#3b2417"}
- "especial": un dibujo ya hecho (alien, perro...) o una imagen que haya subido un admin.
      {"tipo": "especial", "id": "alien"}      {"tipo": "especial", "id": "subido-3"}

El backend solo valida y guarda; los dibujos los pinta la app. El catálogo
(GET /api/avatares) es la única fuente de las opciones válidas, así la app y el
backend no se desincronizan.
"""
import random
import re

from .errores import ErrorApi
from .extensions import db
from .models import AvatarSubido

PIELES = ["#fde0c8", "#f1c27d", "#e0ac69", "#c68642", "#8d5524", "#5c3a21"]
COLORES_PELO = ["#1c1c1c", "#3b2417", "#6a4027", "#a0632f", "#e3c16f", "#b5482a", "#9e9e9e", "#f2f2f2",
                "#2f6fdb", "#e0408a"]
PEINADOS = ["calvo", "rapado", "corto", "tupe", "rizos", "melena", "cresta"]
BARBAS = ["ninguna", "bigote", "perilla", "completa"]
# Dibujos incluidos en la app. Los que suba un admin van en la tabla AvatarSubido.
ESPECIALES = {"alien": "Alien", "perro": "Perro", "gato": "Gato", "pepino": "Pepino", "calabaza": "Calabaza"}

PREFIJO_SUBIDO = "subido-"
_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def persona_aleatoria(rng=None):
    rng = rng or random.SystemRandom()
    pelo = rng.choice(COLORES_PELO[:8])  # al azar, colores de pelo "normales"
    return {
        "tipo": "persona",
        "piel": rng.choice(PIELES),
        "peinado": rng.choice(PEINADOS),
        "color_pelo": pelo,
        "barba": rng.choice(BARBAS),
        "color_barba": pelo,
    }


def _subido_activo(avatar_id):
    numero = avatar_id[len(PREFIJO_SUBIDO):]
    if not numero.isascii() or not numero.isdigit() or len(numero) > 9:
        return False
    subido = db.session.get(AvatarSubido, int(numero))
    return subido is not None and subido.activo


def validar_avatar(datos):
    """Devuelve el avatar normalizado (solo con los campos conocidos) o lanza 400."""
    if not isinstance(datos, dict):
        raise ErrorApi(400, "Avatar no válido")
    tipo = datos.get("tipo")

    if tipo == "persona":
        avatar = {"tipo": "persona"}
        for campo, opciones in (("peinado", PEINADOS), ("barba", BARBAS)):
            if datos.get(campo) not in opciones:
                raise ErrorApi(400, f"Avatar no válido: '{campo}' debe ser uno de {', '.join(opciones)}")
            avatar[campo] = datos[campo]
        for campo in ("piel", "color_pelo", "color_barba"):
            color = datos.get(campo)
            if not isinstance(color, str) or not _COLOR.match(color):
                raise ErrorApi(400, f"Avatar no válido: '{campo}' debe ser un color tipo #a1b2c3")
            avatar[campo] = color.lower()
        return avatar

    if tipo == "especial":
        avatar_id = datos.get("id")
        if not isinstance(avatar_id, str):
            raise ErrorApi(400, "Avatar no válido")
        if avatar_id in ESPECIALES or (avatar_id.startswith(PREFIJO_SUBIDO) and _subido_activo(avatar_id)):
            return {"tipo": "especial", "id": avatar_id}
        raise ErrorApi(400, "Ese avatar no existe")

    raise ErrorApi(400, "Avatar no válido: 'tipo' debe ser 'persona' o 'especial'")


# ------------------------------------------------------------ imágenes subidas por un admin
MAX_BYTES_IMAGEN = 300 * 1024

# Solo imágenes "de mapa de bits". SVG no: puede llevar código dentro.
_FIRMAS = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
)


def tipo_de_imagen(contenido):
    """Detecta el formato mirando los primeros bytes (no nos fiamos de la extensión)."""
    for firma, mime in _FIRMAS:
        if contenido.startswith(firma):
            return mime
    if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "image/webp"
    return None
