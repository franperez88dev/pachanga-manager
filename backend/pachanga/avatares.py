"""Avatares de los jugadores.

Un avatar se guarda como un pequeño JSON en el usuario. Hay dos tipos:

- "persona": un muñeco que el jugador personaliza.
      {"tipo": "persona", "piel": "#e0ac69", "peinado": "tupe", "color_pelo": "#3b2417",
       "barba": "perilla", "color_barba": "#3b2417"}
- "especial": uno de los dibujos ya hechos (alien, perro, gato...).
      {"tipo": "especial", "id": "alien"}

El backend solo valida y guarda; los dibujos los pinta la app. El catálogo
(GET /api/avatares) es la única fuente de las opciones válidas, así la app y el
backend no se desincronizan.
"""
import random
import re

from .errores import ErrorApi

PIELES = ["#fde0c8", "#f1c27d", "#e0ac69", "#c68642", "#8d5524", "#5c3a21"]
COLORES_PELO = ["#1c1c1c", "#3b2417", "#6a4027", "#a0632f", "#e3c16f", "#b5482a", "#9e9e9e", "#f2f2f2",
                "#2f6fdb", "#e0408a"]
PEINADOS = ["calvo", "corto", "tupe", "rizos", "melena", "cresta"]
BARBAS = ["ninguna", "bigote", "perilla", "completa"]
# Dibujos especiales incluidos en la app
ESPECIALES = {"alien": "Alien", "perro": "Perro", "gato": "Gato", "pepino": "Pepino", "calabaza": "Calabaza"}

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
        if not isinstance(datos.get("id"), str) or datos["id"] not in ESPECIALES:
            raise ErrorApi(400, "Ese avatar no existe")
        return {"tipo": "especial", "id": datos["id"]}

    raise ErrorApi(400, "Avatar no válido: 'tipo' debe ser 'persona' o 'especial'")
