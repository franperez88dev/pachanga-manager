"""Flujo completo: partido, convocatoria, equipos, cierre con resultado, goles y clasificación."""


def crear_partido(client, admin, **datos):
    datos = {"fecha": "2026-10-04T19:00", "lugar": "Polideportivo", **datos}
    return client.post("/api/partidos", json=datos, headers=admin.headers)


def test_crear_partido_valida_datos(client, admin):
    assert crear_partido(client, admin).status_code == 201
    assert crear_partido(client, admin, fecha="mañana").status_code == 400
    assert crear_partido(client, admin, lugar="   ").status_code == 400


def test_convocatoria_exige_exactamente_10_distintos_y_aprobados(client, admin, plantilla, nuevo):
    pid = crear_partido(client, admin).get_json()["partido"]["id"]
    ids = [j.id for j in plantilla]

    def convocar(lista):
        return client.put(f"/api/partidos/{pid}/convocatoria", json={"jugadores": lista}, headers=admin.headers)

    assert convocar(ids[:9]).status_code == 400
    assert convocar(ids[:11]).status_code == 400
    assert convocar(ids[:9] + [ids[0]]).status_code == 400
    pendiente = nuevo("Pendiente", estado="pendiente")
    assert convocar(ids[:9] + [pendiente.id]).status_code == 400
    assert convocar(ids[:9] + [99999]).status_code == 400
    r = convocar(ids[:10])
    assert r.status_code == 200
    assert r.get_json()["partido"]["num_convocados"] == 10


def test_no_se_hacen_equipos_sin_10_convocados(client, admin):
    pid = crear_partido(client, admin).get_json()["partido"]["id"]
    assert client.post(f"/api/partidos/{pid}/equipos", json={}, headers=admin.headers).status_code == 409


def test_equipos_blanco_y_negro_con_nombres_y_fuerza(client, admin, plantilla, partido_con_equipos):
    p = client.get(f"/api/partidos/{partido_con_equipos}", headers=plantilla[0].headers).get_json()["partido"]
    eq = p["equipos"]
    assert eq["blanco"]["nombre"] == "Nevados C.F."
    assert eq["negro"]["nombre"] == "Sombras F.C."
    assert len(eq["blanco"]["jugadores"]) == len(eq["negro"]["jugadores"]) == 5
    assert eq["diferencia"] == round(abs(eq["blanco"]["fuerza"] - eq["negro"]["fuerza"]), 1)
    # El jugador ve en qué equipo está; aún no hay resultado
    assert p["convocado"] is True and p["mi_equipo"] in ("blanco", "negro")
    assert p["resultado"] is None


def test_rebarajar_cambia_el_reparto(client, admin, plantilla, partido_con_equipos):
    pid = partido_con_equipos
    # Valoraciones variadas para que haya repartos más y menos igualados
    for i, j in enumerate(plantilla[:10]):
        client.post("/api/valoraciones", json={"valorado_id": j.id, "estrellas": i % 5 + 1},
                    headers=plantilla[11].headers)

    def reparto():
        p = client.get(f"/api/partidos/{pid}", headers=admin.headers).get_json()["partido"]
        return frozenset({frozenset(x["id"] for x in p["equipos"][c]["jugadores"]) for c in ("blanco", "negro")})

    client.post(f"/api/partidos/{pid}/equipos", json={}, headers=admin.headers)
    for _ in range(10):
        antes = reparto()
        r = client.post(f"/api/partidos/{pid}/equipos", json={"rebarajar": True}, headers=admin.headers)
        assert r.status_code == 200
        assert reparto() != antes


def test_volver_a_elegir_deshace_los_equipos_y_mantiene_convocatoria(client, admin, partido_con_equipos):
    r = client.delete(f"/api/partidos/{partido_con_equipos}/equipos", headers=admin.headers)
    p = r.get_json()["partido"]
    assert p["equipos"] is None and p["equipos_generados"] is False
    assert p["num_convocados"] == 10


# ------------------------------------------------------------ cerrar con resultado
def test_cerrar_exige_resultado(client, admin, partido_con_equipos):
    url = f"/api/partidos/{partido_con_equipos}/cerrar"
    assert client.post(url, json={}, headers=admin.headers).status_code == 400
    assert client.post(url, json={"goles_blanco": -1, "goles_negro": 2}, headers=admin.headers).status_code == 400
    r = client.post(url, json={"goles_blanco": 4, "goles_negro": 4}, headers=admin.headers)
    assert r.status_code == 200
    p = r.get_json()["partido"]
    assert p["estado"] == "cerrado" and p["resultado"] == {"blanco": 4, "negro": 4}


def test_corregir_resultado(client, admin, partido_cerrado):
    r = client.put(f"/api/partidos/{partido_cerrado}/resultado", json={"goles_blanco": 5, "goles_negro": 2},
                   headers=admin.headers)
    assert r.get_json()["partido"]["resultado"] == {"blanco": 5, "negro": 2}


def test_partido_cerrado_no_se_modifica(client, admin, partido_cerrado):
    pid = partido_cerrado
    assert client.post(f"/api/partidos/{pid}/equipos", json={}, headers=admin.headers).status_code == 409
    assert client.put(f"/api/partidos/{pid}/convocatoria", json={"jugadores": []},
                      headers=admin.headers).status_code == 409
    assert client.delete(f"/api/partidos/{pid}", headers=admin.headers).status_code == 409


# ------------------------------------------------------------ camino A: planilla del admin
def equipos_de(client, admin, pid):
    p = client.get(f"/api/partidos/{pid}", headers=admin.headers).get_json()["partido"]
    return ([j["id"] for j in p["equipos"]["blanco"]["jugadores"]],
            [j["id"] for j in p["equipos"]["negro"]["jugadores"]])


def test_planilla_solo_con_partido_cerrado(client, admin, partido_con_equipos):
    url = f"/api/partidos/{partido_con_equipos}/estadisticas"
    assert client.get(url, headers=admin.headers).status_code == 409
    assert client.put(url, json={"jugadores": []}, headers=admin.headers).status_code == 409


def test_planilla_del_admin_confirma_todo_y_cuadra(client, admin, plantilla, partido_cerrado):
    """3-2: el Blanco marca 2 goles propios + 1 gpp de un negro; el Negro marca 2."""
    pid = partido_cerrado
    blancos, negros = equipos_de(client, admin, pid)
    planilla = [
        {"id": blancos[0], "goles": 2, "gpp": 0, "asistencias": 0},
        {"id": blancos[1], "goles": 0, "gpp": 0, "asistencias": 2},
        {"id": negros[0], "goles": 2, "gpp": 1, "asistencias": 0},
        {"id": negros[1], "goles": 0, "gpp": 0, "asistencias": 1},
    ]
    r = client.put(f"/api/partidos/{pid}/estadisticas", json={"jugadores": planilla}, headers=admin.headers)
    assert r.status_code == 200
    datos = r.get_json()
    assert datos["avisos"] == []
    assert len(datos["jugadores"]) == 10
    fila = {j["id"]: j for j in datos["jugadores"]}
    assert (fila[negros[0]]["goles"], fila[negros[0]]["gpp"]) == (2, 1)
    assert fila[blancos[2]]["goles"] == 0  # no apuntado = 0
    # Queda confirmado: sube directamente a la clasificación, sin pasar otra vez por el admin
    tabla = client.get("/api/clasificacion?orden=gpp", headers=admin.headers).get_json()["clasificacion"]
    assert tabla[0]["id"] == negros[0] and tabla[0]["gpp"] == 1
    assert client.get("/api/admin/reportes", headers=admin.headers).get_json()["reportes"] == []


def test_planilla_que_no_cuadra_se_guarda_con_avisos(client, admin, partido_cerrado):
    pid = partido_cerrado
    blancos, _ = equipos_de(client, admin, pid)
    planilla = [{"id": blancos[0], "goles": 1, "gpp": 0, "asistencias": 3}]
    r = client.put(f"/api/partidos/{pid}/estadisticas", json={"jugadores": planilla}, headers=admin.headers)
    assert r.status_code == 200
    avisos = " ".join(r.get_json()["avisos"])
    assert "el Blanco suman 1" in avisos and "dice 3" in avisos
    assert "el Negro suman 0" in avisos
    assert "más asistencias" in avisos


def test_planilla_valida_jugadores_y_numeros(client, admin, plantilla, partido_cerrado):
    url = f"/api/partidos/{partido_cerrado}/estadisticas"
    no_convocado = plantilla[11].id
    blanco = equipos_de(client, admin, partido_cerrado)[0][0]
    malas = [
        [{"id": no_convocado, "goles": 1, "gpp": 0, "asistencias": 0}],
        [{"id": blanco, "goles": 1, "gpp": 0, "asistencias": 0}] * 2,
        [{"id": blanco, "goles": -1, "gpp": 0, "asistencias": 0}],
        [{"id": blanco, "goles": 1, "asistencias": 0}],  # falta gpp
        [{"id": True, "goles": 1, "gpp": 0, "asistencias": 0}],
    ]
    for planilla in malas:
        assert client.put(url, json={"jugadores": planilla}, headers=admin.headers).status_code == 400


def test_la_planilla_sustituye_a_lo_anterior(client, admin, plantilla, partido_cerrado):
    """Si un jugador ya había apuntado algo, la planilla del admin manda."""
    pid = partido_cerrado
    j = plantilla[0]
    client.post(f"/api/partidos/{pid}/reportes", json={"goles": 5, "asistencias": 0}, headers=j.headers)
    ver = client.get(f"/api/partidos/{pid}/estadisticas", headers=admin.headers).get_json()
    fila = next(f for f in ver["jugadores"] if f["id"] == j.id)
    assert fila["goles"] == 0 and fila["pendiente"] == {"goles": 5, "gpp": 0, "asistencias": 0}

    client.put(f"/api/partidos/{pid}/estadisticas",
               json={"jugadores": [{"id": j.id, "goles": 2, "gpp": 0, "asistencias": 0}]}, headers=admin.headers)
    perfil = client.get(f"/api/jugadores/{j.id}", headers=j.headers).get_json()["jugador"]
    assert perfil["goles"] == 2
    assert client.get("/api/admin/reportes", headers=admin.headers).get_json()["reportes"] == []


# ------------------------------------------------------------ camino B: "Sig." y cada uno lo suyo
def test_no_se_reporta_hasta_que_el_admin_cierra(client, plantilla, partido_con_equipos):
    r = client.post(f"/api/partidos/{partido_con_equipos}/reportes", json={"goles": 1, "asistencias": 0},
                    headers=plantilla[0].headers)
    assert r.status_code == 409


def test_flujo_reportes_de_jugadores_y_clasificacion(client, admin, plantilla, partido_cerrado):
    pid = partido_cerrado
    goleador, asistente, tramposo, despistado = plantilla[0], plantilla[1], plantilla[2], plantilla[3]
    url = f"/api/partidos/{pid}/reportes"

    reportes = [
        (client.post(url, json={"goles": 3, "asistencias": 1}, headers=goleador.headers), "confirmar"),
        (client.post(url, json={"goles": 0, "asistencias": 4}, headers=asistente.headers), "confirmar"),
        (client.post(url, json={"goles": 9, "asistencias": 0}, headers=tramposo.headers), "descartar"),
        (client.post(url, json={"goles": 0, "gpp": 1, "asistencias": 0}, headers=despistado.headers), "confirmar"),
    ]
    assert {resp.status_code for resp, _ in reportes} == {201}
    # Un segundo reporte del mismo partido no se permite mientras el primero siga vivo
    assert client.post(url, json={"goles": 1, "asistencias": 0}, headers=goleador.headers).status_code == 409

    assert len(client.get("/api/admin/reportes", headers=admin.headers).get_json()["reportes"]) == 4
    for resp, accion in reportes:
        id_reporte = resp.get_json()["reporte"]["id"]
        assert client.post(f"/api/admin/reportes/{id_reporte}/{accion}", headers=admin.headers).status_code == 200

    def tabla(orden):
        return client.get(f"/api/clasificacion?orden={orden}", headers=admin.headers).get_json()["clasificacion"]

    fila = {f["mote"]: f for f in tabla("goles")}
    assert (fila["Feragi"]["goles"], fila["Feragi"]["asistencias"], fila["Feragi"]["partidos"]) == (3, 1, 1)
    assert fila["El Tanke"]["goles"] == 0 and fila["El Tanke"]["partidos"] == 1  # descartado no cuenta
    assert fila["Rulo"]["gpp"] == 1
    assert fila["Guaje"]["partidos"] == 0  # no convocado
    assert tabla("goles")[0]["mote"] == "Feragi"
    assert tabla("asistencias")[0]["mote"] == "Chuti"
    assert tabla("gpp")[0]["mote"] == "Rulo"
    assert all(f["partidos"] == 1 for f in tabla("partidos")[:10])
    assert client.get("/api/clasificacion?orden=dorsal", headers=admin.headers).status_code == 400

    perfil = client.get(f"/api/jugadores/{goleador.id}", headers=plantilla[5].headers).get_json()["jugador"]
    assert (perfil["goles"], perfil["asistencias"], perfil["gpp"], perfil["partidos"]) == (3, 1, 0, 1)


def test_anular_reporte_pendiente_propio(client, plantilla, partido_cerrado, admin):
    j = plantilla[0]
    url = f"/api/partidos/{partido_cerrado}/reportes"
    id_reporte = client.post(url, json={"goles": 1, "asistencias": 0}, headers=j.headers).get_json()["reporte"]["id"]
    r = client.post(f"/api/reportes/{id_reporte}/anular", headers=j.headers)
    assert r.status_code == 200 and r.get_json()["reporte"]["estado"] == "anulado"
    assert client.get("/api/admin/reportes", headers=admin.headers).get_json()["reportes"] == []
    assert client.post(url, json={"goles": 2, "asistencias": 0}, headers=j.headers).status_code == 201


def test_no_se_anula_un_reporte_ya_confirmado(client, plantilla, partido_cerrado, admin):
    j = plantilla[0]
    id_reporte = client.post(f"/api/partidos/{partido_cerrado}/reportes", json={"goles": 1, "asistencias": 0},
                             headers=j.headers).get_json()["reporte"]["id"]
    client.post(f"/api/admin/reportes/{id_reporte}/confirmar", headers=admin.headers)
    assert client.post(f"/api/reportes/{id_reporte}/anular", headers=j.headers).status_code == 409


def test_reporte_valida_numeros(client, plantilla, partido_cerrado):
    h = plantilla[0].headers
    url = f"/api/partidos/{partido_cerrado}/reportes"
    assert client.post(url, json={"goles": 0, "asistencias": 0}, headers=h).status_code == 400
    assert client.post(url, json={"goles": -1, "asistencias": 0}, headers=h).status_code == 400
    assert client.post(url, json={"goles": "2", "asistencias": 0}, headers=h).status_code == 400
    assert client.post(url, json={"goles": 1, "gpp": -1, "asistencias": 0}, headers=h).status_code == 400


# ------------------------------------------------------------ varios
def test_proximo_partido(client, admin, plantilla):
    h = plantilla[0].headers
    assert client.get("/api/partidos/proximo", headers=h).get_json() == {"partido": None}
    crear_partido(client, admin, fecha="2026-10-11T19:00", lugar="Lejano")
    crear_partido(client, admin, fecha="2026-10-04T19:00", lugar="Cercano")
    assert client.get("/api/partidos/proximo", headers=h).get_json()["partido"]["lugar"] == "Cercano"


def test_health_no_necesita_sesion(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.get_json() == {"estado": "ok"}


def test_cors_permite_la_app_capacitor(client):
    r = client.get("/health", headers={"Origin": "https://localhost"})
    assert r.headers.get("Access-Control-Allow-Origin") == "https://localhost"
    r = client.get("/health", headers={"Origin": "https://malvado.example"})
    assert "Access-Control-Allow-Origin" not in r.headers
