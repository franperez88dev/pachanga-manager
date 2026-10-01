"""Avatares: personalizables y especiales."""
import pytest

from pachanga.avatares import BARBAS, ESPECIALES, PEINADOS, validar_avatar

PERSONA = {"tipo": "persona", "piel": "#E0AC69", "peinado": "tupe", "color_pelo": "#3b2417",
           "barba": "perilla", "color_barba": "#3b2417"}


def test_catalogo_publico(client):
    r = client.get("/api/avatares")
    assert r.status_code == 200
    datos = r.get_json()
    assert datos["peinados"] == PEINADOS and datos["barbas"] == BARBAS
    assert {e["id"] for e in datos["especiales"]} == set(ESPECIALES)
    assert datos["pieles"] and datos["colores_pelo"]


def test_registro_con_avatar_personalizado(client):
    r = client.post("/api/auth/registro", json={"mote": "Kike", "avatar": PERSONA})
    assert r.status_code == 201
    assert r.get_json()["usuario"]["avatar"] == {**PERSONA, "piel": "#e0ac69"}


def test_registro_sin_avatar_le_toca_uno_al_azar_valido(client):
    avatar = client.post("/api/auth/registro", json={"mote": "Kike"}).get_json()["usuario"]["avatar"]
    assert validar_avatar(avatar) == avatar


def test_registro_con_avatar_especial(client):
    r = client.post("/api/auth/registro", json={"mote": "Kike", "avatar": {"tipo": "especial", "id": "pepino"}})
    assert r.get_json()["usuario"]["avatar"] == {"tipo": "especial", "id": "pepino"}


@pytest.mark.parametrize("malo", [
    "alien", {"tipo": "robot"},
    {**PERSONA, "peinado": "mohicano-galactico"},
    {**PERSONA, "peinado": "rapado"},
    {**PERSONA, "barba": "corta"},
    {**PERSONA, "barba": None},
    {**PERSONA, "piel": "rojo"},
    {**PERSONA, "color_pelo": "#12345"},
    {**PERSONA, "color_barba": "#zzzzzz"},
    {"tipo": "especial", "id": "dragon"},
    {"tipo": "especial", "id": "subido-1"},
    {"tipo": "especial", "id": ["alien"]},
])
def test_avatares_no_validos(client, malo):
    r = client.post("/api/auth/registro", json={"mote": "Kike", "avatar": malo})
    assert r.status_code == 400


def test_campos_desconocidos_se_descartan(client):
    r = client.post("/api/auth/registro", json={"mote": "Kike", "avatar": {**PERSONA, "script": "<b>"}})
    assert "script" not in r.get_json()["usuario"]["avatar"]


def test_cambiar_mi_avatar(client, nuevo):
    j = nuevo("Feragi")
    r = client.put("/api/yo/avatar", json={"avatar": {"tipo": "especial", "id": "gato"}}, headers=j.headers)
    assert r.status_code == 200
    assert r.get_json()["usuario"]["avatar"]["id"] == "gato"
    assert client.put("/api/yo/avatar", json={"avatar": {"tipo": "especial", "id": "x"}},
                      headers=j.headers).status_code == 400
    assert client.put("/api/yo/avatar", json={"avatar": PERSONA}).status_code == 401


def test_ya_no_se_pueden_subir_avatares(client, admin):
    assert client.post("/api/admin/avatares", headers=admin.headers).status_code in (404, 405)


def test_peticion_gigante_se_corta(client):
    r = client.post("/api/auth/registro", data=b"x" * (2 * 1024 * 1024), content_type="application/json")
    assert r.status_code == 413
