"""Reparto equilibrado de 10 jugadores en dos equipos de 5.

Hay C(10,5) = 252 formas de elegir 5 jugadores, pero cada reparto aparece dos veces
({A|B} y {B|A} son el mismo partido con los petos cambiados). Recorremos las 252 y
nos quedamos con las 126 que contienen al primer jugador: así cada reparto sale una vez.

TOLERANCIA de "Rebarajar" (config TOLERANCIA_REBARAJAR, 0,5 por defecto):
las fuerzas son sumas de 5 medias de 1 a 5 estrellas (unos 15 puntos por equipo).
Media estrella de diferencia total equivale a 0,1 estrellas por jugador, algo
imperceptible en el campo, y con 10 jugadores deja normalmente varios repartos
entre los que elegir. La tolerancia se mide respecto al MEJOR reparto posible
(diferencia <= mejor + tolerancia), así sigue funcionando aunque ningún reparto
quede perfectamente igualado. Si no hay ningún candidato distinto del anterior
dentro de la tolerancia, se coge el siguiente reparto más igualado.
"""
import random
from dataclasses import dataclass
from itertools import combinations

TAM_EQUIPO = 5
JUGADORES_POR_PARTIDO = TAM_EQUIPO * 2
MEDIA_SIN_DATOS = 3.0  # si todavía no hay ni una valoración en toda la peña
_EPS = 1e-9  # margen para comparar números decimales


@dataclass(frozen=True)
class Reparto:
    equipo_a: frozenset
    equipo_b: frozenset
    fuerza_a: float
    fuerza_b: float

    @property
    def diferencia(self):
        return abs(self.fuerza_a - self.fuerza_b)

    @property
    def clave(self):
        """Identifica el reparto sin importar qué equipo es el blanco y cuál el negro."""
        return frozenset({self.equipo_a, self.equipo_b})


def medias_con_provisional(medias, ids):
    """Completa las medias de los jugadores sin valoraciones con la media global.

    `medias`: {id: media} solo de los jugadores que tienen alguna valoración.
    `media global`: media de todas esas medias; si no hay ninguna, MEDIA_SIN_DATOS.
    """
    global_ = sum(medias.values()) / len(medias) if medias else MEDIA_SIN_DATOS
    return {i: medias.get(i, global_) for i in ids}


def repartos_posibles(fuerzas):
    """Todos los repartos distintos (126) de los 10 jugadores de `fuerzas` {id: media}."""
    ids = sorted(fuerzas)
    if len(ids) != JUGADORES_POR_PARTIDO:
        raise ValueError(f"Hacen falta exactamente {JUGADORES_POR_PARTIDO} jugadores")
    todos = frozenset(ids)
    repartos = []
    for combo in combinations(ids, TAM_EQUIPO):  # las 252 combinaciones
        if ids[0] not in combo:
            continue  # es el espejo de otro reparto que ya contamos
        a = frozenset(combo)
        b = todos - a
        repartos.append(Reparto(a, b, sum(fuerzas[i] for i in a), sum(fuerzas[i] for i in b)))
    return repartos


def elegir_reparto(fuerzas, anterior=None, tolerancia=0.5, rng=None):
    """Devuelve (blanco, negro, fuerza_blanco, fuerza_negro).

    - Sin `anterior` (botón "Crear equipos"): uno de los repartos más igualados posibles.
    - Con `anterior` (botón "Rebarajar"): uno al azar dentro de la tolerancia y
      NUNCA igual al anterior. `anterior` es una pareja (equipo1, equipo2) de conjuntos de ids.
    `rng` permite pasar un generador con semilla en los tests.
    """
    rng = rng or random.SystemRandom()
    repartos = repartos_posibles(fuerzas)
    mejor = min(r.diferencia for r in repartos)

    if anterior is None:
        candidatos = [r for r in repartos if r.diferencia <= mejor + _EPS]
    else:
        clave_anterior = frozenset(frozenset(e) for e in anterior)
        distintos = [r for r in repartos if r.clave != clave_anterior]
        candidatos = [r for r in distintos if r.diferencia <= mejor + tolerancia + _EPS]
        if not candidatos:
            siguiente = min(r.diferencia for r in distintos)
            candidatos = [r for r in distintos if r.diferencia <= siguiente + _EPS]

    elegido = rng.choice(candidatos)
    # Qué mitad lleva el peto blanco también se sortea
    if rng.random() < 0.5:
        return elegido.equipo_a, elegido.equipo_b, elegido.fuerza_a, elegido.fuerza_b
    return elegido.equipo_b, elegido.equipo_a, elegido.fuerza_b, elegido.fuerza_a
