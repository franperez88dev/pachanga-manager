"""Flujo completo: partido, convocatoria, equipos, cierre, goles y clasificación."""


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
    # El jugador ve en qué equipo está
    assert p["convocado"] is True and p["mi_equipo"] in ("blanco", "negro")


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


def test_flujo_goles_confirmados_y_clasificacion(client, admin, plantilla, partido_con_equipos):
    pid = partido_con_equipos
    goleador, asistente, tramposo = plantilla[0], plantilla[1], plantilla[2]

    r1 = client.post(f"/api/partidos/{pid}/reportes", json={"goles": 3, "asistencias": 1}, headers=goleador.headers)
    r2 = client.post(f"/api/partidos/{pid}/reportes", json={"goles": 0, "asistencias": 4}, headers=asistente.headers)
    r3 = client.post(f"/api/partidos/{pid}/reportes", json={"goles": 9, "asistencias": 0}, headers=tramposo.headers)
    assert r1.status_code == r2.status_code == r3.status_code == 201
    # Un segundo reporte del mismo partido no se permite mientras el primero siga vivo
    assert client.post(f"/api/partidos/{pid}/reportes", json={"goles": 1, "asistencias": 0},
                       headers=goleador.headers).status_code == 409

    pendientes = client.get("/api/admin/reportes", headers=admin.headers).get_json()["reportes"]
    assert len(pendientes) == 3
    client.post(f"/api/admin/reportes/{r1.get_json()['reporte']['id']}/confirmar", headers=admin.headers)
    client.post(f"/api/admin/reportes/{r2.get_json()['reporte']['id']}/confirmar", headers=admin.headers)
    client.post(f"/api/admin/reportes/{r3.get_json()['reporte']['id']}/descartar", headers=admin.headers)

    def fila(mote, orden="goles"):
        tabla = client.get(f"/api/clasificacion?orden={orden}", headers=admin.headers).get_json()["clasificacion"]
        return next(f for f in tabla if f["mote"] == mote), tabla

    # Partido aún abierto: no cuenta nada
    assert fila("Feragi")[0]["goles"] == 0
    assert client.post(f"/api/partidos/{pid}/cerrar", headers=admin.headers).status_code == 200

    feragi, tabla = fila("Feragi")
    assert (feragi["goles"], feragi["asistencias"], feragi["partidos"]) == (3, 1, 1)
    assert tabla[0]["mote"] == "Feragi"
    assert fila("Chuti", "asistencias")[1][0]["mote"] == "Chuti"
    assert fila("El Tanke")[0]["goles"] == 0  # descartado no cuenta
    assert fila("El Tanke")[0]["partidos"] == 1  # pero el partido jugado sí
    assert fila("Guaje")[0]["partidos"] == 0  # no convocado
    # Orden por partidos: los 10 convocados primero
    tabla_pj = fila("Feragi", "partidos")[1]
    assert all(f["partidos"] == 1 for f in tabla_pj[:10])
    assert client.get("/api/clasificacion?orden=dorsal", headers=admin.headers).status_code == 400

    perfil = client.get(f"/api/jugadores/{goleador.id}", headers=plantilla[5].headers).get_json()["jugador"]
    assert (perfil["goles"], perfil["asistencias"], perfil["partidos"]) == (3, 1, 1)


def test_anular_reporte_pendiente_propio(client, plantilla, partido_con_equipos, admin):
    j = plantilla[0]
    rid = client.post(f"/api/partidos/{partido_con_equipos}/reportes", json={"goles": 1, "asistencias": 0},
                      headers=j.headers).get_json()["reporte"]["id"]
    r = client.post(f"/api/reportes/{rid}/anular", headers=j.headers)
    assert r.status_code == 200 and r.get_json()["reporte"]["estado"] == "anulado"
    # Ya no está pendiente para el admin, y puede volver a reportar
    assert client.get("/api/admin/reportes", headers=admin.headers).get_json()["reportes"] == []
    assert client.post(f"/api/partidos/{partido_con_equipos}/reportes", json={"goles": 2, "asistencias": 0},
                       headers=j.headers).status_code == 201


def test_no_se_anula_un_reporte_ya_confirmado(client, plantilla, partido_con_equipos, admin):
    j = plantilla[0]
    rid = client.post(f"/api/partidos/{partido_con_equipos}/reportes", json={"goles": 1, "asistencias": 0},
                      headers=j.headers).get_json()["reporte"]["id"]
    client.post(f"/api/admin/reportes/{rid}/confirmar", headers=admin.headers)
    assert client.post(f"/api/reportes/{rid}/anular", headers=j.headers).status_code == 409


def test_reporte_valida_numeros(client, plantilla, partido_con_equipos):
    h = plantilla[0].headers
    url = f"/api/partidos/{partido_con_equipos}/reportes"
    assert client.post(url, json={"goles": 0, "asistencias": 0}, headers=h).status_code == 400
    assert client.post(url, json={"goles": -1, "asistencias": 0}, headers=h).status_code == 400
    assert client.post(url, json={"goles": "2", "asistencias": 0}, headers=h).status_code == 400


def test_partido_cerrado_no_se_modifica(client, admin, plantilla, partido_con_equipos):
    pid = partido_con_equipos
    client.post(f"/api/partidos/{pid}/cerrar", headers=admin.headers)
    assert client.post(f"/api/partidos/{pid}/equipos", json={}, headers=admin.headers).status_code == 409
    assert client.put(f"/api/partidos/{pid}/convocatoria", json={"jugadores": []},
                      headers=admin.headers).status_code == 409
    assert client.delete(f"/api/partidos/{pid}", headers=admin.headers).status_code == 409


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
