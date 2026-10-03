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


def votar(client, jugadores, pid, cambiar=True):
    for j in jugadores:
        r = client.post(f"/api/partidos/{pid}/voto", json={"cambiar": cambiar}, headers=j.headers)
        assert r.status_code == 200, r.get_json()
    return r.get_json()["partido"]["votacion"]


def rebarajar(client, admin, pid):
    return client.post(f"/api/partidos/{pid}/equipos", json={"rebarajar": True}, headers=admin.headers)


def test_crear_equipos_solo_una_vez(client, admin, partido_con_equipos):
    r = client.post(f"/api/partidos/{partido_con_equipos}/equipos", json={}, headers=admin.headers)
    assert r.status_code == 409


def test_rebarajar_exige_6_votos_a_favor(client, admin, plantilla, partido_con_equipos):
    pid = partido_con_equipos
    convocados = plantilla[:10]
    assert rebarajar(client, admin, pid).status_code == 409  # sin votos
    votar(client, convocados[:4], pid, cambiar=False)
    v = votar(client, convocados[4:9], pid, cambiar=True)  # 5 síes: aún no
    assert (v["votos_si"], v["votos_no"], v["se_puede_rebarajar"]) == (5, 4, False)
    assert rebarajar(client, admin, pid).status_code == 409
    v = votar(client, convocados[9:10], pid, cambiar=True)  # 6 síes frente a 4 noes: mayoría
    assert (v["votos_si"], v["votos_no"], v["se_puede_rebarajar"]) == (6, 4, True)
    assert rebarajar(client, admin, pid).status_code == 200


def test_se_vota_una_sola_vez_por_reparto(client, admin, plantilla, partido_con_equipos):
    pid = partido_con_equipos
    url = f"/api/partidos/{pid}/voto"
    assert client.post(url, json={"cambiar": False}, headers=plantilla[0].headers).status_code == 200
    # Ni repetir ni cambiar de opinión
    assert client.post(url, json={"cambiar": True}, headers=plantilla[0].headers).status_code == 409
    assert client.post(url, json={"cambiar": False}, headers=plantilla[0].headers).status_code == 409
    v = client.get(f"/api/partidos/{pid}", headers=plantilla[0].headers).get_json()["partido"]["votacion"]
    assert (v["votos_si"], v["votos_no"], v["mi_voto"]) == (0, 1, False)
    # Tras un nuevo reparto, puede volver a votar
    votar(client, plantilla[1:7], pid)
    assert rebarajar(client, admin, pid).status_code == 200
    assert client.post(url, json={"cambiar": True}, headers=plantilla[0].headers).status_code == 200


def test_maximo_3_repartos_y_votacion_nueva_en_cada_uno(client, admin, plantilla, partido_con_equipos):
    pid = partido_con_equipos
    convocados = plantilla[:10]
    # Valoraciones variadas para que haya repartos más y menos igualados
    for i, j in enumerate(convocados):
        client.post("/api/valoraciones", json={"valorado_id": j.id, "estrellas": i % 5 + 1},
                    headers=plantilla[11].headers)

    def reparto():
        p = client.get(f"/api/partidos/{pid}", headers=admin.headers).get_json()["partido"]
        return frozenset({frozenset(x["id"] for x in p["equipos"][c]["jugadores"]) for c in ("blanco", "negro")})

    for numero in (2, 3):
        antes = reparto()
        votar(client, convocados[:6], pid)
        r = rebarajar(client, admin, pid)
        assert r.status_code == 200
        assert reparto() != antes
        v = r.get_json()["partido"]["votacion"]
        assert v["repartos_hechos"] == numero and v["votos_si"] == 0  # los votos de antes ya no cuentan

    assert v["abierta"] is False
    r = client.post(f"/api/partidos/{pid}/voto", json={"cambiar": True}, headers=convocados[0].headers)
    assert r.status_code == 409
    assert rebarajar(client, admin, pid).status_code == 409


def test_solo_votan_convocados_y_con_equipos(client, admin, plantilla, partido_con_equipos):
    r = client.post(f"/api/partidos/{partido_con_equipos}/voto", json={"cambiar": True},
                   headers=plantilla[11].headers)
    assert r.status_code == 403
    r = client.post(f"/api/partidos/{partido_con_equipos}/voto", json={"cambiar": "si"},
                   headers=plantilla[0].headers)
    assert r.status_code == 400
    sin_equipos = crear_partido(client, admin).get_json()["partido"]["id"]
    client.put(f"/api/partidos/{sin_equipos}/convocatoria", json={"jugadores": [j.id for j in plantilla[:10]]},
               headers=admin.headers)
    assert client.post(f"/api/partidos/{sin_equipos}/voto", json={"cambiar": True},
                      headers=plantilla[0].headers).status_code == 409


def test_la_lista_avisa_de_votacion_pendiente(client, admin, plantilla, partido_con_equipos):
    def debo_votar(j):
        partidos = client.get("/api/partidos", headers=j.headers).get_json()["partidos"]
        return next(p for p in partidos if p["id"] == partido_con_equipos)["debo_votar"]

    assert debo_votar(plantilla[0]) is True
    votar(client, plantilla[:1], partido_con_equipos)
    assert debo_votar(plantilla[0]) is False
    assert debo_votar(plantilla[11]) is False  # no convocado


def test_cada_uno_ve_su_voto_pero_no_el_de_los_demas(client, plantilla, partido_con_equipos):
    pid = partido_con_equipos
    votar(client, plantilla[:1], pid, cambiar=True)
    votar(client, plantilla[1:2], pid, cambiar=False)
    v0 = client.get(f"/api/partidos/{pid}", headers=plantilla[0].headers).get_json()["partido"]["votacion"]
    v2 = client.get(f"/api/partidos/{pid}", headers=plantilla[2].headers).get_json()["partido"]["votacion"]
    assert v0["mi_voto"] is True and v2["mi_voto"] is None
    assert (v2["votos_si"], v2["votos_no"]) == (1, 1)


def test_formacion_1_2_2_en_cada_equipo(client, admin, partido_con_equipos):
    p = client.get(f"/api/partidos/{partido_con_equipos}", headers=admin.headers).get_json()["partido"]
    for color in ("blanco", "negro"):
        equipo = p["equipos"][color]
        posiciones = [j["posicion"] for j in equipo["jugadores"]]
        assert posiciones == ["portero", "defensa", "defensa", "delantero", "delantero"]
        # Orden en portería: los 5, sin repetir, y empieza el que está de portero
        assert sorted(j["orden_porteria"] for j in equipo["jugadores"]) == [1, 2, 3, 4, 5]
        assert sorted(equipo["porteria"]) == sorted(j["id"] for j in equipo["jugadores"])
        assert equipo["porteria"][0] == equipo["jugadores"][0]["id"]


def test_asistencias_son_opcionales(client, admin, plantilla, partido_cerrado):
    """De momento la app no usa asistencias: se puede apuntar sin ellas."""
    r = client.post(f"/api/partidos/{partido_cerrado}/reportes", json={"goles": 1}, headers=plantilla[0].headers)
    assert r.status_code == 201 and r.get_json()["reporte"]["asistencias"] == 0
    blanco = equipos_de(client, admin, partido_cerrado)[0][0]
    r = client.put(f"/api/partidos/{partido_cerrado}/estadisticas",
                   json={"jugadores": [{"id": blanco, "goles": 3}]}, headers=admin.headers)
    assert r.status_code == 200


def test_volver_a_elegir_con_los_mismos_10_no_cambia_los_equipos(client, admin, plantilla, partido_con_equipos):
    """Así "Volver a elegir" no sirve para saltarse la votación."""
    pid = partido_con_equipos
    antes = client.get(f"/api/partidos/{pid}", headers=admin.headers).get_json()["partido"]["equipos"]
    r = client.put(f"/api/partidos/{pid}/convocatoria", json={"jugadores": [j.id for j in reversed(plantilla[:10])]},
                   headers=admin.headers)
    assert r.get_json()["partido"]["equipos"] == antes


def test_cambiar_un_convocado_empieza_de_cero(client, admin, plantilla, partido_con_equipos):
    pid = partido_con_equipos
    votar(client, plantilla[:7], pid)
    nuevos = [j.id for j in plantilla[:9]] + [plantilla[11].id]
    p = client.put(f"/api/partidos/{pid}/convocatoria", json={"jugadores": nuevos},
                   headers=admin.headers).get_json()["partido"]
    assert p["equipos"] is None and p["votacion"] is None and p["num_convocados"] == 10
    r = client.post(f"/api/partidos/{pid}/equipos", json={}, headers=admin.headers)
    v = r.get_json()["partido"]["votacion"]
    assert (v["repartos_hechos"], v["votos_si"]) == (1, 0)


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
    assert "Faltan goles de Nevados C.F.: hay 1" in avisos and "el resultado es 3" in avisos
    assert "Faltan goles de Sombras F.C.: hay 0" in avisos
    assert "más asistencias" in avisos


def test_planilla_no_admite_mas_goles_que_el_resultado(client, admin, partido_cerrado):
    """3-2: si el Blanco suma 4 (entre goles propios y gpp del rival), no se puede guardar."""
    pid = partido_cerrado
    blancos, negros = equipos_de(client, admin, pid)
    url = f"/api/partidos/{pid}/estadisticas"
    demasiados = [{"id": blancos[0], "goles": 3, "gpp": 0}, {"id": negros[0], "goles": 0, "gpp": 1}]
    r = client.put(url, json={"jugadores": demasiados}, headers=admin.headers)
    assert r.status_code == 400 and "Nevados C.F. tendría 4 goles" in r.get_json()["error"]
    # Justo el resultado sí vale (y que falten también)
    justos = [{"id": blancos[0], "goles": 2, "gpp": 0}, {"id": negros[0], "goles": 0, "gpp": 1}]
    assert client.put(url, json={"jugadores": justos}, headers=admin.headers).status_code == 200


def test_planilla_valida_jugadores_y_numeros(client, admin, plantilla, partido_cerrado):
    url = f"/api/partidos/{partido_cerrado}/estadisticas"
    no_convocado = plantilla[11].id
    blanco = equipos_de(client, admin, partido_cerrado)[0][0]
    malas = [
        [{"id": no_convocado, "goles": 1, "gpp": 0, "asistencias": 0}],
        [{"id": blanco, "goles": 1, "gpp": 0, "asistencias": 0}] * 2,
        [{"id": blanco, "goles": -1, "gpp": 0, "asistencias": 0}],
        [{"id": blanco, "gpp": 0}],  # faltan los goles
        [{"id": True, "goles": 1, "gpp": 0, "asistencias": 0}],
    ]
    for planilla in malas:
        assert client.put(url, json={"jugadores": planilla}, headers=admin.headers).status_code == 400


def test_la_planilla_sustituye_a_lo_anterior(client, admin, plantilla, partido_cerrado):
    """Si un jugador ya había apuntado algo, la planilla del admin manda."""
    pid = partido_cerrado
    j = plantilla[0]
    assert client.post(f"/api/partidos/{pid}/reportes", json={"goles": 2, "asistencias": 0},
                       headers=j.headers).status_code == 201
    ver = client.get(f"/api/partidos/{pid}/estadisticas", headers=admin.headers).get_json()
    fila = next(f for f in ver["jugadores"] if f["id"] == j.id)
    assert fila["goles"] == 0 and fila["pendiente"] == {"goles": 2, "gpp": 0, "asistencias": 0}

    client.put(f"/api/partidos/{pid}/estadisticas",
               json={"jugadores": [{"id": j.id, "goles": 1, "gpp": 0, "asistencias": 0}]}, headers=admin.headers)
    perfil = client.get(f"/api/jugadores/{j.id}", headers=j.headers).get_json()["jugador"]
    assert perfil["goles"] == 1
    assert client.get("/api/admin/reportes", headers=admin.headers).get_json()["reportes"] == []


# ------------------------------------------------------------ camino B: "Sig." y cada uno lo suyo
def test_no_se_reporta_hasta_que_el_admin_cierra(client, plantilla, partido_con_equipos):
    r = client.post(f"/api/partidos/{partido_con_equipos}/reportes", json={"goles": 1, "asistencias": 0},
                    headers=plantilla[0].headers)
    assert r.status_code == 409


def test_flujo_reportes_de_jugadores_y_clasificacion(client, admin, plantilla, partido_cerrado):
    pid = partido_cerrado
    # Resultado amplio: aquí se prueba el flujo, no el límite de goles
    client.put(f"/api/partidos/{pid}/resultado", json={"goles_blanco": 15, "goles_negro": 15}, headers=admin.headers)
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




# ------------------------------------------------------------ nunca más goles que el resultado
def test_jugador_no_puede_apuntar_mas_goles_que_el_resultado(client, plantilla, partido_cerrado):
    """3-2: nadie puede apuntarse 4 goles (su equipo tendría más que el resultado)."""
    r = client.post(f"/api/partidos/{partido_cerrado}/reportes", json={"goles": 4}, headers=plantilla[0].headers)
    assert r.status_code == 400 and "más goles que en el resultado" in r.get_json()["error"]


def test_admin_no_puede_confirmar_un_reporte_que_pase_del_resultado(client, admin, plantilla, partido_cerrado):
    """3-2: dos del Blanco apuntan 2 goles cada uno. Cada reporte cabe por separado,
    pero al confirmar el segundo el Blanco tendría 4: se bloquea."""
    pid = partido_cerrado
    blancos, _ = equipos_de(client, admin, pid)
    por_id = {j.id: j for j in plantilla}
    ids_reportes = []
    for uid in blancos[:2]:
        r = client.post(f"/api/partidos/{pid}/reportes", json={"goles": 2}, headers=por_id[uid].headers)
        assert r.status_code == 201
        ids_reportes.append(r.get_json()["reporte"]["id"])
    assert client.post(f"/api/admin/reportes/{ids_reportes[0]}/confirmar", headers=admin.headers).status_code == 200
    r = client.post(f"/api/admin/reportes/{ids_reportes[1]}/confirmar", headers=admin.headers)
    assert r.status_code == 409 and "Nevados C.F. tendría 4 goles" in r.get_json()["error"]
    # Descartarlo sí se puede
    assert client.post(f"/api/admin/reportes/{ids_reportes[1]}/descartar", headers=admin.headers).status_code == 200
    # Y un tercero del Blanco ya no puede ni enviar 2 goles (2 confirmados + 2 > 3)
    r = client.post(f"/api/partidos/{pid}/reportes", json={"goles": 2}, headers=por_id[blancos[2]].headers)
    assert r.status_code == 400
