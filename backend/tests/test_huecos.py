"""Reservar y liberar hueco, reservas, multas y el texto del precio."""
from datetime import timedelta

import pytest

from pachanga.models import Multa
from pachanga.servicios import ahora_local


def ver(client, pid, quien):
    return client.get(f"/api/partidos/{pid}", headers=quien.headers).get_json()["partido"]


def motes(partido, reserva):
    return [j["mote"] for j in partido["apuntados"] if j["reserva"] is reserva]


@pytest.fixture
def partido_en(client, admin):
    """partido_en(horas): crea un partido que empieza dentro de esas horas. Devuelve su id."""
    def _crear(horas):
        fecha = (ahora_local() + timedelta(hours=horas)).isoformat(timespec="minutes")
        r = client.post("/api/partidos", json={"fecha": fecha, "lugar": "Polideportivo"}, headers=admin.headers)
        return r.get_json()["partido"]["id"]
    return _crear


# ------------------------------------------------------------ reservar hueco
def test_los_10_primeros_juegan_y_los_siguientes_son_reservas(client, plantilla, partido_abierto, apuntar):
    pid = partido_abierto
    p = apuntar(pid, plantilla)  # se apuntan los 12, en orden
    assert (p["plazas"], p["num_apuntados"], p["num_reservas"]) == (10, 12, 2)
    # La lista va numerada por orden de llegada: del 1 al 10 juegan, 11 y 12 son reservas
    assert [j["puesto"] for j in p["apuntados"]] == list(range(1, 13))
    assert motes(p, reserva=False) == [j.mote for j in plantilla[:10]]
    assert motes(p, reserva=True) == ["Manu", "Guaje"]

    primero = ver(client, pid, plantilla[0])
    assert (primero["apuntado"], primero["mi_puesto"], primero["convocado"], primero["soy_reserva"]) == (
        True, 1, True, False)
    ultimo = ver(client, pid, plantilla[11])
    assert (ultimo["apuntado"], ultimo["mi_puesto"], ultimo["convocado"], ultimo["soy_reserva"]) == (
        True, 12, False, True)


def test_quien_no_esta_apuntado_lo_ve_asi(client, admin, plantilla, partido_abierto, apuntar):
    apuntar(partido_abierto, plantilla[:3])
    p = ver(client, partido_abierto, plantilla[5])
    assert (p["apuntado"], p["mi_puesto"], p["convocado"], p["soy_reserva"]) == (False, None, False, False)
    assert p["lista_cerrada"] is False and p["multa_si_libero"] is False


def test_no_te_puedes_apuntar_dos_veces(client, plantilla, partido_abierto, apuntar):
    apuntar(partido_abierto, plantilla[:1])
    r = client.post(f"/api/partidos/{partido_abierto}/hueco", headers=plantilla[0].headers)
    assert r.status_code == 409 and "Ya estás apuntado" in r.get_json()["error"]


def test_el_admin_tambien_se_apunta_como_uno_mas(client, admin, partido_abierto):
    r = client.post(f"/api/partidos/{partido_abierto}/hueco", headers=admin.headers)
    assert r.status_code == 201 and r.get_json()["partido"]["mi_puesto"] == 1


# ------------------------------------------------------------ liberar hueco
def test_liberar_con_tiempo_no_lleva_multa_y_sube_el_primer_reserva(client, plantilla, partido_abierto, apuntar):
    pid = partido_abierto
    apuntar(pid, plantilla)
    assert ver(client, pid, plantilla[3])["multa_si_libero"] is False
    r = client.delete(f"/api/partidos/{pid}/hueco", headers=plantilla[3].headers)
    assert r.status_code == 200 and r.get_json()["multa"] is False
    p = r.get_json()["partido"]
    assert p["apuntado"] is False and p["num_apuntados"] == 11
    # Manu (primer reserva) pasa a jugar con el puesto 10; Guaje sigue de reserva, ahora el 11
    assert motes(p, reserva=False)[-1] == "Manu" and motes(p, reserva=True) == ["Guaje"]
    assert ver(client, pid, plantilla[10])["convocado"] is True
    assert Multa.query.count() == 0
    # Y puede volver a apuntarse: entra el último
    r = client.post(f"/api/partidos/{pid}/hueco", headers=plantilla[3].headers)
    assert r.get_json()["partido"]["mi_puesto"] == 12


def test_no_puedes_liberar_un_hueco_que_no_tienes(client, plantilla, partido_abierto):
    r = client.delete(f"/api/partidos/{partido_abierto}/hueco", headers=plantilla[0].headers)
    assert r.status_code == 409


@pytest.mark.parametrize("horas,multa", [(25, False), (23, True), (1, True), (-1, True)])
def test_liberar_con_menos_de_24_horas_lleva_multa(client, admin, plantilla, partido_en, apuntar, horas, multa):
    pid = partido_en(horas)
    apuntar(pid, plantilla[:10])
    j = plantilla[0]
    assert ver(client, pid, j)["multa_si_libero"] is multa  # la app avisa antes de pulsar
    r = client.delete(f"/api/partidos/{pid}/hueco", headers=j.headers)
    assert r.status_code == 200 and r.get_json()["multa"] is multa
    mias = client.get("/api/multas/mias", headers=j.headers).get_json()["multas"]
    assert len(mias) == (1 if multa else 0)
    if multa:
        assert mias[0]["estado"] == "pendiente" and mias[0]["partido"]["id"] == pid
        assert mias[0]["jugador"]["id"] == j.id and "24 horas" in mias[0]["motivo"]


def test_la_multa_se_pone_aunque_un_reserva_ocupe_el_sitio(client, plantilla, partido_en, apuntar):
    pid = partido_en(5)
    apuntar(pid, plantilla)  # 10 + 2 reservas
    r = client.delete(f"/api/partidos/{pid}/hueco", headers=plantilla[0].headers)
    assert r.get_json()["multa"] is True
    assert r.get_json()["partido"]["num_apuntados"] == 11 and Multa.query.count() == 1


def test_un_reserva_se_borra_sin_multa_aunque_falte_poco(client, plantilla, partido_en, apuntar):
    pid = partido_en(5)
    apuntar(pid, plantilla)
    reserva = plantilla[11]
    assert ver(client, pid, reserva)["multa_si_libero"] is False
    r = client.delete(f"/api/partidos/{pid}/hueco", headers=reserva.headers)
    assert r.status_code == 200 and r.get_json()["multa"] is False and Multa.query.count() == 0


# ------------------------------------------------------------ con los equipos hechos, la lista se cierra
def test_con_equipos_los_jugadores_ya_no_se_apuntan_ni_se_borran(client, admin, plantilla, partido_con_equipos):
    pid = partido_con_equipos
    assert ver(client, pid, plantilla[0])["lista_cerrada"] is True
    assert ver(client, pid, plantilla[0])["multa_si_libero"] is False  # ni siquiera puede liberar
    r = client.delete(f"/api/partidos/{pid}/hueco", headers=plantilla[0].headers)
    assert r.status_code == 409 and "avisa al admin" in r.get_json()["error"]
    r = client.post(f"/api/partidos/{pid}/hueco", headers=plantilla[11].headers)
    assert r.status_code == 409 and "lista está cerrada" in r.get_json()["error"]


def test_los_equipos_se_hacen_con_los_10_primeros_y_los_reservas_no_juegan(
        client, admin, plantilla, partido_abierto, apuntar):
    pid = partido_abierto
    apuntar(pid, plantilla)
    r = client.post(f"/api/partidos/{pid}/equipos", json={}, headers=admin.headers)
    assert r.status_code == 200
    p = r.get_json()["partido"]
    en_equipos = {j["id"] for c in ("blanco", "negro") for j in p["equipos"][c]["jugadores"]}
    assert en_equipos == {j.id for j in plantilla[:10]}
    assert motes(p, reserva=True) == ["Manu", "Guaje"]
    assert all(j["equipo"] is None for j in p["apuntados"] if j["reserva"])

    # Un reserva no vota ni apunta goles, y el partido no le cuenta como jugado
    reserva = plantilla[10]
    assert client.post(f"/api/partidos/{pid}/voto", json={"cambiar": True}, headers=reserva.headers).status_code == 403
    assert ver(client, pid, reserva)["debo_votar"] is False
    client.post(f"/api/partidos/{pid}/cerrar", json={"goles_blanco": 2, "goles_negro": 1}, headers=admin.headers)
    assert client.post(f"/api/partidos/{pid}/reportes", json={"goles": 1}, headers=reserva.headers).status_code == 403
    planilla = client.get(f"/api/partidos/{pid}/estadisticas", headers=admin.headers).get_json()
    assert len(planilla["jugadores"]) == 10
    assert client.put(f"/api/partidos/{pid}/estadisticas", json={"jugadores": [{"id": reserva.id, "goles": 1}]},
                      headers=admin.headers).status_code == 400
    perfil = lambda j: client.get(f"/api/jugadores/{j.id}", headers=admin.headers).get_json()["jugador"]
    assert perfil(reserva)["partidos"] == 0 and perfil(plantilla[0])["partidos"] == 1


# ------------------------------------------------------------ el admin gestiona la lista
def test_el_admin_apunta_a_un_jugador(client, admin, plantilla, nuevo, partido_abierto):
    url = f"/api/partidos/{partido_abierto}/jugadores"
    r = client.post(url, json={"user_id": plantilla[4].id}, headers=admin.headers)
    assert r.status_code == 201 and motes(r.get_json()["partido"], reserva=False) == ["Kike"]
    assert client.post(url, json={"user_id": plantilla[4].id}, headers=admin.headers).status_code == 409
    pendiente = nuevo("Pendiente", estado="pendiente")
    assert client.post(url, json={"user_id": pendiente.id}, headers=admin.headers).status_code == 404
    assert client.post(url, json={"user_id": 99999}, headers=admin.headers).status_code == 404
    assert client.post(url, json={"user_id": "4"}, headers=admin.headers).status_code == 400


def test_el_admin_quita_a_un_jugador_con_o_sin_multa(client, admin, plantilla, partido_abierto, apuntar):
    pid = partido_abierto
    apuntar(pid, plantilla[:10])
    sin, con = plantilla[0], plantilla[1]
    r = client.delete(f"/api/partidos/{pid}/jugadores/{sin.id}", json={}, headers=admin.headers)
    assert r.status_code == 200 and r.get_json()["partido"]["num_apuntados"] == 9
    r = client.delete(f"/api/partidos/{pid}/jugadores/{con.id}", json={"multa": True}, headers=admin.headers)
    assert r.status_code == 200 and r.get_json()["partido"]["num_apuntados"] == 8
    assert client.get("/api/multas/mias", headers=sin.headers).get_json()["multas"] == []
    multas = client.get("/api/multas/mias", headers=con.headers).get_json()["multas"]
    assert len(multas) == 1 and "admin" in multas[0]["motivo"]
    # Quitar a quien no está apuntado: 404
    assert client.delete(f"/api/partidos/{pid}/jugadores/{sin.id}", json={},
                         headers=admin.headers).status_code == 404


def test_quitar_a_uno_que_juega_con_equipos_hechos_sube_al_reserva(client, admin, plantilla, partido_con_equipos):
    pid = partido_con_equipos
    # Con la lista cerrada, a un jugador nuevo solo lo puede apuntar el admin, y entra de reserva
    r = client.post(f"/api/partidos/{pid}/jugadores", json={"user_id": plantilla[10].id}, headers=admin.headers)
    p = r.get_json()["partido"]
    assert p["equipos"] is not None and motes(p, reserva=True) == ["Manu"]

    r = client.delete(f"/api/partidos/{pid}/jugadores/{plantilla[2].id}", json={"multa": True}, headers=admin.headers)
    p = r.get_json()["partido"]
    # Los equipos se deshacen, Manu pasa a jugar y la lista se vuelve a abrir hasta que el admin cree equipos
    assert p["equipos"] is None and p["lista_cerrada"] is False
    assert motes(p, reserva=True) == [] and "Manu" in motes(p, reserva=False) and p["num_apuntados"] == 10
    assert client.post(f"/api/partidos/{pid}/equipos", json={}, headers=admin.headers).status_code == 200


def test_quitar_a_un_reserva_no_deshace_los_equipos(client, admin, plantilla, partido_con_equipos):
    pid = partido_con_equipos
    client.post(f"/api/partidos/{pid}/jugadores", json={"user_id": plantilla[10].id}, headers=admin.headers)
    antes = ver(client, pid, admin)["equipos"]
    r = client.delete(f"/api/partidos/{pid}/jugadores/{plantilla[10].id}", json={}, headers=admin.headers)
    assert r.get_json()["partido"]["equipos"] == antes


# ------------------------------------------------------------ multas (panel del admin)
def test_el_admin_marca_las_multas_como_pagadas_o_perdonadas(client, admin, plantilla, partido_en, apuntar):
    pid = partido_en(3)
    apuntar(pid, plantilla[:10])
    for j in plantilla[:2]:
        client.delete(f"/api/partidos/{pid}/hueco", headers=j.headers)
    multas = client.get("/api/admin/multas", headers=admin.headers).get_json()["multas"]
    assert {m["jugador"]["mote"] for m in multas} == {"Feragi", "Chuti"}
    assert {m["estado"] for m in multas} == {"pendiente"}

    def poner(mid, estado):
        return client.put(f"/api/admin/multas/{mid}", json={"estado": estado}, headers=admin.headers)

    assert poner(multas[0]["id"], "pagada").get_json()["multa"]["estado"] == "pagada"
    assert poner(multas[1]["id"], "perdonada").get_json()["multa"]["estado"] == "perdonada"
    assert poner(multas[0]["id"], "pendiente").get_json()["multa"]["estado"] == "pendiente"  # deshacer
    assert poner(multas[0]["id"], "regalada").status_code == 400
    assert poner(99999, "pagada").status_code == 404
    # El jugador ve el cambio en las suyas
    suya = client.get("/api/multas/mias", headers=plantilla[0].headers).get_json()["multas"][0]
    assert suya["estado"] in ("pendiente", "perdonada")


def test_borrar_el_partido_borra_sus_multas(client, admin, plantilla, partido_en, apuntar):
    pid = partido_en(3)
    apuntar(pid, plantilla[:10])
    client.delete(f"/api/partidos/{pid}/hueco", headers=plantilla[0].headers)
    assert Multa.query.count() == 1
    assert client.delete(f"/api/partidos/{pid}", headers=admin.headers).status_code == 204
    assert Multa.query.count() == 0


# ------------------------------------------------------------ texto del precio
def test_el_admin_pone_y_cambia_el_texto_del_precio(client, admin, plantilla):
    texto = "Pagar a Feragi (2,2 € anticipado | 2,5 € el día del partido)"
    r = client.post("/api/partidos", json={"fecha": "2040-06-02T19:00", "lugar": "Pista", "info_pago": texto},
                    headers=admin.headers)
    p = r.get_json()["partido"]
    assert r.status_code == 201 and p["info_pago"] == texto
    pid = p["id"]
    # Lo ve cualquier jugador, también en la lista de partidos
    assert ver(client, pid, plantilla[0])["info_pago"] == texto
    assert client.get("/api/partidos", headers=plantilla[0].headers).get_json()["partidos"][0]["info_pago"] == texto

    def editar(**cambios):
        return client.patch(f"/api/partidos/{pid}", json=cambios, headers=admin.headers)

    assert editar(info_pago="3 € por cabeza").get_json()["partido"]["info_pago"] == "3 € por cabeza"
    assert editar(lugar="Otra pista").get_json()["partido"]["info_pago"] == "3 € por cabeza"  # no se pierde
    assert editar(info_pago="x" * 201).status_code == 400
    assert editar(info_pago="   ").get_json()["partido"]["info_pago"] is None  # vacío = sin texto


def test_partido_sin_texto_de_precio(client, admin):
    r = client.post("/api/partidos", json={"fecha": "2040-06-02T19:00", "lugar": "Pista"}, headers=admin.headers)
    assert r.get_json()["partido"]["info_pago"] is None
