"""Nadie ve el PIN de nadie ni valoraciones (ni estrellas ni medias), tampoco el admin.
El PIN solo aparece al registrarse (al propio usuario) y cuando un admin genera uno nuevo.
El dorsal es público (es el número de la camiseta)."""
import json

import pytest

PALABRAS_PROHIBIDAS = ("pin", "hash", "stars", "estrellas", "media", "rating", "valoracion")


def claves(obj):
    """Todas las claves de un JSON anidado."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from claves(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from claves(v)


def assert_sin_datos_secretos(respuesta):
    assert respuesta.status_code < 400, respuesta.get_json()
    for k in claves(respuesta.get_json()):
        assert not any(p in k.lower() for p in PALABRAS_PROHIBIDAS), f"Clave sospechosa: {k}"


@pytest.fixture
def peña_con_valoraciones(client, admin, plantilla, partido_con_equipos):
    """Todos valoran a todos, se vota y se rebaraja, se cierra el partido y hay un reporte pendiente."""
    for j in plantilla:
        for otro in plantilla:
            if otro.id != j.id:
                client.post("/api/valoraciones", json={"valorado_id": otro.id, "estrellas": 4}, headers=j.headers)
    pid = partido_con_equipos
    for j in plantilla[:6]:
        client.post(f"/api/partidos/{pid}/voto", json={"cambiar": True}, headers=j.headers)
    assert client.post(f"/api/partidos/{pid}/equipos", json={"rebarajar": True},
                       headers=admin.headers).status_code == 200
    client.post(f"/api/partidos/{pid}/cerrar", json={"goles_blanco": 1, "goles_negro": 0}, headers=admin.headers)
    r = client.post(f"/api/partidos/{pid}/reportes", json={"goles": 1, "asistencias": 0},
                    headers=plantilla[0].headers)
    assert r.status_code == 201
    return pid


def rutas_de_consulta(pid, uid):
    return ["/api/yo", "/api/jugadores", f"/api/jugadores/{uid}", "/api/clasificacion",
            "/api/partidos", "/api/partidos/proximo", f"/api/partidos/{pid}",
            "/api/valoraciones/mias", "/api/reportes/mios"]


def test_ninguna_consulta_de_jugador_devuelve_pines_ni_valoraciones(client, plantilla, peña_con_valoraciones):
    jugador = plantilla[0]
    for ruta in rutas_de_consulta(peña_con_valoraciones, plantilla[1].id):
        assert_sin_datos_secretos(client.get(ruta, headers=jugador.headers))


def test_ni_siquiera_el_admin_ve_pines_ni_valoraciones(client, admin, plantilla, peña_con_valoraciones):
    pid = peña_con_valoraciones
    rutas = rutas_de_consulta(pid, plantilla[1].id) + [
        "/api/admin/altas", "/api/admin/usuarios", "/api/admin/reportes", f"/api/partidos/{pid}/estadisticas"]
    for ruta in rutas:
        assert_sin_datos_secretos(client.get(ruta, headers=admin.headers))


def test_el_pin_solo_se_ve_al_registrarse(client):
    r = client.post("/api/auth/registro", json={"mote": "Nuevo"})
    pin = r.get_json()["pin"]
    login = client.post("/api/auth/login", json={"mote": "Nuevo", "pin": pin})
    assert login.status_code == 200
    assert '"pin"' not in json.dumps(login.get_json())


def test_el_dorsal_es_publico(client, plantilla):
    jugadores = client.get("/api/jugadores", headers=plantilla[0].headers).get_json()["jugadores"]
    assert {j["mote"]: j["dorsal"] for j in jugadores}["Chuti"] == plantilla[1].dorsal


def test_equipos_muestran_solo_fuerza_total(client, plantilla, peña_con_valoraciones):
    partido = client.get(f"/api/partidos/{peña_con_valoraciones}", headers=plantilla[0].headers).get_json()["partido"]
    equipos = partido["equipos"]
    assert set(equipos) == {"blanco", "negro", "diferencia"}
    for color in ("blanco", "negro"):
        assert set(equipos[color]) == {"color", "nombre", "fuerza", "jugadores", "porteria"}
        for j in equipos[color]["jugadores"]:
            assert set(j) == {"id", "mote", "nombre_real", "dorsal", "es_admin", "avatar", "posicion",
                              "orden_porteria"}

# ------------------------------------------------------------ reglas de las valoraciones
def test_valoracion_una_sola_vez_y_sin_poder_verla(client, plantilla):
    a, b = plantilla[0], plantilla[1]
    r = client.post("/api/valoraciones", json={"valorado_id": b.id, "estrellas": 5}, headers=a.headers)
    assert r.status_code == 201
    r = client.post("/api/valoraciones", json={"valorado_id": b.id, "estrellas": 1}, headers=a.headers)
    assert r.status_code == 409
    assert client.get("/api/valoraciones/mias", headers=a.headers).get_json() == {"valorados": [b.id]}


def test_no_puedes_valorarte_a_ti_mismo(client, plantilla):
    a = plantilla[0]
    r = client.post("/api/valoraciones", json={"valorado_id": a.id, "estrellas": 5}, headers=a.headers)
    assert r.status_code == 400


@pytest.mark.parametrize("estrellas", [0, 6, "5", 3.5, True, None])
def test_estrellas_entre_1_y_5(client, plantilla, estrellas):
    r = client.post("/api/valoraciones", json={"valorado_id": plantilla[1].id, "estrellas": estrellas},
                    headers=plantilla[0].headers)
    assert r.status_code == 400


def test_no_se_valora_a_pendientes(client, plantilla, nuevo):
    pendiente = nuevo("Pendiente", estado="pendiente")
    r = client.post("/api/valoraciones", json={"valorado_id": pendiente.id, "estrellas": 3},
                    headers=plantilla[0].headers)
    assert r.status_code == 404


def test_restriccion_unique_en_base_de_datos(app, plantilla):
    """Aunque alguien se saltara la API, la base de datos rechaza la valoración repetida."""
    from sqlalchemy.exc import IntegrityError
    from pachanga.extensions import db
    from pachanga.models import Rating

    db.session.add(Rating(rater_id=plantilla[0].id, rated_id=plantilla[1].id, stars=3))
    db.session.commit()
    db.session.add(Rating(rater_id=plantilla[0].id, rated_id=plantilla[1].id, stars=4))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
