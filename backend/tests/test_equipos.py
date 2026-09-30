"""Tests del algoritmo de equipos (sin base de datos)."""
import random
from itertools import combinations

import pytest

from pachanga.equipos import (
    MEDIA_SIN_DATOS, elegir_reparto, medias_con_provisional, repartos_posibles,
)

FUERZAS = {1: 3.0, 2: 4.25, 3: 3.0, 4: 4.75, 5: 2.33, 6: 3.67, 7: 2.67, 8: 3.67, 9: 3.33, 10: 4.0}


def diferencia_optima_por_fuerza_bruta(fuerzas):
    """Cálculo independiente y "tonto" de la mejor diferencia posible (las 252)."""
    ids = list(fuerzas)
    total = sum(fuerzas.values())
    return min(abs(2 * sum(fuerzas[i] for i in c) - total) for c in combinations(ids, 5))


def test_hay_126_repartos_distintos_de_las_252_combinaciones():
    repartos = repartos_posibles(FUERZAS)
    assert len(repartos) == 126
    assert len({r.clave for r in repartos}) == 126
    for r in repartos:
        assert len(r.equipo_a) == len(r.equipo_b) == 5
        assert r.equipo_a | r.equipo_b == set(FUERZAS)


def test_crear_equipos_da_el_reparto_mas_igualado():
    for semilla in range(20):
        blanco, negro, fb, fn = elegir_reparto(FUERZAS, rng=random.Random(semilla))
        assert len(blanco) == len(negro) == 5
        assert blanco.isdisjoint(negro)
        assert abs(fb - fn) == pytest.approx(diferencia_optima_por_fuerza_bruta(FUERZAS))
        assert fb == pytest.approx(sum(FUERZAS[i] for i in blanco))


def test_rebarajar_nunca_repite_el_reparto_anterior_y_es_equilibrado():
    rng = random.Random(1)
    blanco, negro, _, _ = elegir_reparto(FUERZAS, rng=rng)
    mejor = diferencia_optima_por_fuerza_bruta(FUERZAS)
    vistos = set()
    for _ in range(50):
        nb, nn, fb, fn = elegir_reparto(FUERZAS, anterior=(blanco, negro), tolerancia=0.5, rng=rng)
        assert frozenset({nb, nn}) != frozenset({frozenset(blanco), frozenset(negro)})
        assert abs(fb - fn) <= mejor + 0.5 + 1e-9
        vistos.add(frozenset({nb, nn}))
        blanco, negro = nb, nn
    assert len(vistos) > 1, "Rebarajar debería dar repartos variados"


def test_rebarajar_sin_candidatos_en_tolerancia_coge_el_siguiente_mas_igualado():
    # Potencias de 2: todas las sumas son distintas, así que el mejor reparto es único
    fuerzas = {i: float(2 ** i) for i in range(10)}
    diferencias = sorted(r.diferencia for r in repartos_posibles(fuerzas))
    b, n, fb, fn = elegir_reparto(fuerzas, rng=random.Random(0))
    assert abs(fb - fn) == diferencias[0]
    nb, nn, fb2, fn2 = elegir_reparto(fuerzas, anterior=(b, n), tolerancia=0.0, rng=random.Random(0))
    assert frozenset({nb, nn}) != frozenset({b, n})
    assert abs(fb2 - fn2) == diferencias[1]


def test_colores_se_sortean():
    colores = set()
    for semilla in range(30):
        blanco, _, _, _ = elegir_reparto(FUERZAS, rng=random.Random(semilla))
        colores.add(1 in blanco)
    assert colores == {True, False}


def test_jugador_sin_valoraciones_usa_la_media_global():
    medias = {1: 4.0, 2: 2.0}
    completas = medias_con_provisional(medias, [1, 2, 3])
    assert completas == {1: 4.0, 2: 2.0, 3: 3.0}


def test_sin_ninguna_valoracion_usa_media_neutra():
    assert medias_con_provisional({}, [1, 2]) == {1: MEDIA_SIN_DATOS, 2: MEDIA_SIN_DATOS}


@pytest.mark.parametrize("n", [9, 11])
def test_exige_exactamente_10_jugadores(n):
    with pytest.raises(ValueError):
        repartos_posibles({i: 3.0 for i in range(n)})
