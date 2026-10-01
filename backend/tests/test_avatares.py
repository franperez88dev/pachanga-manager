"""Avatares: personalizables, especiales y subidos por un admin."""
import io

import pytest

from pachanga.avatares import BARBAS, ESPECIALES, PEINADOS, validar_avatar

# El PNG más pequeño posible (1x1 píxel transparente)
PNG_MINIMO = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)

PERSONA = {"tipo": "persona", "piel": "#E0AC69", "peinado": "tupe", "color_pelo": "#3b2417",
           "barba": "perilla", "color_barba": "#3b2417"}


def subir(client, admin, nombre="Bicho", contenido=PNG_MINIMO, fichero="b.png"):
    return client.post("/api/admin/avatares", data={"nombre": nombre, "imagen": (io.BytesIO(contenido), fichero)},
                       headers=admin.headers)


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
    {**PERSONA, "barba": None},
    {**PERSONA, "piel": "rojo"},
    {**PERSONA, "color_pelo": "#12345"},
    {**PERSONA, "color_barba": "#zzzzzz"},
    {"tipo": "especial", "id": "dragon"},
    {"tipo": "especial", "id": "subido-999"},
    {"tipo": "especial", "id": "subido-abc"},
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


def test_admin_sube_un_avatar_y_un_jugador_lo_elige(client, admin, nuevo):
    r = subir(client, admin)
    assert r.status_code == 201
    nuevo_avatar = r.get_json()["avatar"]
    assert nuevo_avatar["nombre"] == "Bicho"
    assert nuevo_avatar in client.get("/api/avatares").get_json()["especiales"]

    img = client.get(nuevo_avatar["imagen"])
    assert img.status_code == 200 and img.mimetype == "image/png" and img.data == PNG_MINIMO
    assert img.headers["X-Content-Type-Options"] == "nosniff"

    j = nuevo("Feragi")
    r = client.put("/api/yo/avatar", json={"avatar": {"tipo": "especial", "id": nuevo_avatar["id"]}},
                   headers=j.headers)
    assert r.get_json()["usuario"]["avatar"]["imagen"] == nuevo_avatar["imagen"]


def test_retirar_avatar_lo_quita_del_catalogo_pero_quien_lo_tiene_lo_conserva(client, admin, nuevo):
    subido = subir(client, admin).get_json()["avatar"]
    j = nuevo("Feragi")
    client.put("/api/yo/avatar", json={"avatar": {"tipo": "especial", "id": subido["id"]}}, headers=j.headers)
    numero = subido["imagen"].rsplit("/", 1)[1]
    assert client.delete(f"/api/admin/avatares/{numero}", headers=admin.headers).status_code == 204

    assert subido not in client.get("/api/avatares").get_json()["especiales"]
    assert client.get(subido["imagen"]).status_code == 200
    perfil = client.get(f"/api/jugadores/{j.id}", headers=j.headers).get_json()["jugador"]
    assert perfil["avatar"]["id"] == subido["id"]
    # Pero ya nadie nuevo puede elegirlo
    otro = nuevo("Chuti")
    assert client.put("/api/yo/avatar", json={"avatar": {"tipo": "especial", "id": subido["id"]}},
                      headers=otro.headers).status_code == 400


@pytest.mark.parametrize("contenido,fichero", [
    (b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>", "malo.svg"),
    (b"esto no es una imagen", "texto.png"),
    (PNG_MINIMO + b"\0" * (300 * 1024), "enorme.png"),
], ids=["svg", "texto", "enorme"])
def test_subida_rechaza_lo_que_no_es_imagen_o_pesa_demasiado(client, admin, contenido, fichero):
    assert subir(client, admin, contenido=contenido, fichero=fichero).status_code == 400


def test_subida_exige_nombre(client, admin):
    assert subir(client, admin, nombre="  ").status_code == 400


def test_peticion_gigante_se_corta(client, admin):
    r = subir(client, admin, contenido=PNG_MINIMO + b"\0" * (2 * 1024 * 1024))
    assert r.status_code == 413
