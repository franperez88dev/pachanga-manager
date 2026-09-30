"""Borrado de cuenta desde la app (API) y desde la web (requisito de Google Play)."""
from pachanga.extensions import db
from pachanga.models import MatchPlayer, Rating, StatReport, User


def test_borrado_desde_la_api_elimina_todos_sus_datos(client, admin, plantilla, partido_con_equipos):
    j, otro = plantilla[0], plantilla[1]
    client.post("/api/valoraciones", json={"valorado_id": otro.id, "estrellas": 5}, headers=j.headers)
    client.post("/api/valoraciones", json={"valorado_id": j.id, "estrellas": 2}, headers=otro.headers)
    client.post(f"/api/partidos/{partido_con_equipos}/reportes", json={"goles": 1, "asistencias": 0},
                headers=j.headers)

    assert client.delete("/api/yo", json={}, headers=j.headers).status_code == 400  # falta confirmar
    assert client.delete("/api/yo", json={"confirmar": True}, headers=j.headers).status_code == 204

    assert db.session.get(User, j.id) is None
    assert Rating.query.filter((Rating.rater_id == j.id) | (Rating.rated_id == j.id)).count() == 0
    assert StatReport.query.filter_by(user_id=j.id).count() == 0
    assert MatchPlayer.query.filter_by(user_id=j.id).count() == 0


def test_borrar_un_convocado_deshace_los_equipos_del_partido_abierto(client, admin, plantilla, partido_con_equipos):
    j = plantilla[0]
    client.delete("/api/yo", json={"confirmar": True}, headers=j.headers)
    p = client.get(f"/api/partidos/{partido_con_equipos}", headers=admin.headers).get_json()["partido"]
    assert p["equipos_generados"] is False
    assert p["num_convocados"] == 9


def test_pagina_web_de_borrado(client, nuevo):
    j = nuevo("Feragi")
    assert client.get("/borrar-cuenta").status_code == 200
    # Sin marcar la casilla no borra
    r = client.post("/borrar-cuenta", data={"mote": "Feragi", "dorsal": str(j.dorsal)})
    assert r.status_code == 400 and db.session.get(User, j.id) is not None
    # Dorsal incorrecto: mismo mensaje genérico que en el login
    r = client.post("/borrar-cuenta", data={"mote": "Feragi", "dorsal": "999", "confirmar": "si"})
    assert r.status_code == 401 and db.session.get(User, j.id) is not None
    r = client.post("/borrar-cuenta", data={"mote": "Feragi", "dorsal": str(j.dorsal), "confirmar": "si"})
    assert r.status_code == 200 and "se han borrado" in r.get_data(as_text=True)
    assert db.session.get(User, j.id) is None


def test_pagina_web_escapa_html(client):
    r = client.post("/borrar-cuenta", data={"mote": "<b>x</b>", "dorsal": "1", "confirmar": "si"})
    assert "<b>x</b>" not in r.get_data(as_text=True)
