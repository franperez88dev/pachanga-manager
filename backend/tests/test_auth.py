"""Registro, login con dorsal, bloqueo de intentos y sesión."""
from datetime import timedelta

from pachanga.extensions import db
from pachanga.models import IntentoAcceso, User, ahora
from pachanga.seguridad import MENSAJE_LOGIN_INCORRECTO


def registrar(client, mote, ip="10.0.0.1", **extra):
    return client.post("/api/auth/registro", json={"mote": mote, **extra},
                       environ_base={"REMOTE_ADDR": ip})


def login(client, mote, dorsal, ip="10.0.0.1"):
    return client.post("/api/auth/login", json={"mote": mote, "dorsal": dorsal},
                       environ_base={"REMOTE_ADDR": ip})


# ------------------------------------------------------------ registro y dorsales
def test_registro_asigna_dorsales_correlativos_y_queda_pendiente(client, admin):
    r1 = registrar(client, "Kike", nombre_real="Enrique")
    r2 = registrar(client, "Nino", ip="10.0.0.2")
    assert r1.status_code == 201 and r2.status_code == 201
    assert admin.dorsal == 1
    assert r1.get_json()["dorsal"] == 2
    assert r2.get_json()["dorsal"] == 3
    assert r1.get_json()["usuario"]["estado"] == "pendiente"
    assert r1.get_json()["usuario"]["nombre_real"] == "Enrique"


def test_mote_unico_sin_distinguir_mayusculas(client, admin):
    assert registrar(client, "El Tanke").status_code == 201
    r = registrar(client, "el  TANKE", ip="10.0.0.2")
    assert r.status_code == 409


def test_mote_invalido(client):
    assert registrar(client, "x").status_code == 400
    assert registrar(client, "<script>").status_code == 400
    assert registrar(client, "a" * 21).status_code == 400


def test_dorsales_no_se_reutilizan_tras_rechazo_ni_borrado(client, admin):
    d1 = registrar(client, "Uno").get_json()
    d2 = registrar(client, "Dos").get_json()
    client.post(f"/api/admin/usuarios/{d1['usuario']['id']}/rechazar", headers=admin.headers)
    client.delete("/api/yo", json={"confirmar": True}, headers={"Authorization": f"Bearer {d2['token']}"})
    d3 = registrar(client, "Tres").get_json()
    assert d3["dorsal"] == d2["dorsal"] + 1


def test_limite_de_registros_por_ip(client, app):
    maximo = app.config["REGISTRO_MAX_POR_IP_HORA"]
    for i in range(maximo):
        assert registrar(client, f"Nuevo{i}", ip="9.9.9.9").status_code == 201
    assert registrar(client, "Otro", ip="9.9.9.9").status_code == 429
    assert registrar(client, "Otro", ip="9.9.9.8").status_code == 201


# ------------------------------------------------------------ login
def test_login_con_mote_y_dorsal(client, nuevo):
    j = nuevo("Feragi")
    r = login(client, "feragi", str(j.dorsal))
    assert r.status_code == 200
    datos = r.get_json()
    assert datos["usuario"]["mote"] == "Feragi"
    assert datos["usuario"]["rol"] == "jugador"
    assert "dorsal" not in datos["usuario"]
    # El token funciona
    yo = client.get("/api/yo", headers={"Authorization": f"Bearer {datos['token']}"})
    assert yo.status_code == 200


def test_login_acepta_ceros_a_la_izquierda(client, admin):
    assert login(client, "Fran", "01").status_code == 200
    assert login(client, "Fran", "1").status_code == 200


def test_login_sabe_si_eres_admin(client, admin):
    assert login(client, "Fran", "1").get_json()["usuario"]["rol"] == "admin"


def test_error_identico_para_mote_inexistente_y_dorsal_incorrecto(client, nuevo):
    j = nuevo("Feragi")
    malo_dorsal = login(client, "Feragi", str(j.dorsal + 50), ip="1.1.1.1")
    no_existe = login(client, "Fantasma", "7", ip="1.1.1.2")
    assert malo_dorsal.status_code == no_existe.status_code == 401
    assert malo_dorsal.get_json() == no_existe.get_json() == {"error": MENSAJE_LOGIN_INCORRECTO}


def test_dorsal_no_numerico_es_login_incorrecto(client, nuevo):
    nuevo("Feragi")
    assert login(client, "Feragi", "abc").status_code == 401
    assert login(client, "Feragi", "²").status_code == 401
    assert login(client, "Feragi", "9" * 5000).status_code == 401


def test_bloqueo_por_mote_tras_varios_fallos(client, app, nuevo):
    j = nuevo("Feragi")
    maximo = app.config["LOGIN_MAX_INTENTOS_MOTE"]
    # Cada fallo desde una IP distinta, para probar solo el bloqueo por mote
    for i in range(maximo):
        assert login(client, "Feragi", "999", ip=f"2.0.0.{i}").status_code == 401
    r = login(client, "Feragi", str(j.dorsal), ip="2.0.0.200")
    assert r.status_code == 429, "Bloqueado: ni con el dorsal correcto se entra"
    assert "Retry-After" in r.headers


def test_bloqueo_por_mote_tambien_con_motes_inexistentes(client, app):
    """Si solo se bloquearan motes existentes, el bloqueo delataría quién está registrado."""
    for i in range(app.config["LOGIN_MAX_INTENTOS_MOTE"]):
        login(client, "Fantasma", "1", ip=f"3.0.0.{i}")
    assert login(client, "Fantasma", "1", ip="3.0.0.200").status_code == 429


def test_bloqueo_por_ip_aunque_se_cambie_de_mote(client, app, nuevo):
    j = nuevo("Feragi")
    for i in range(app.config["LOGIN_MAX_INTENTOS_IP"]):
        login(client, f"Mote{i}", "1", ip="4.4.4.4")
    assert login(client, "Feragi", str(j.dorsal), ip="4.4.4.4").status_code == 429
    assert login(client, "Feragi", str(j.dorsal), ip="4.4.4.5").status_code == 200


def test_el_bloqueo_caduca(client, app, nuevo):
    j = nuevo("Feragi")
    for i in range(app.config["LOGIN_MAX_INTENTOS_MOTE"]):
        login(client, "Feragi", "999", ip=f"5.0.0.{i}")
    assert login(client, "Feragi", str(j.dorsal), ip="5.0.0.99").status_code == 429
    # Simulamos que han pasado los minutos de bloqueo
    for registro in IntentoAcceso.query.all():
        if registro.bloqueado_hasta:
            registro.bloqueado_hasta = ahora() - timedelta(seconds=1)
    db.session.commit()
    assert login(client, "Feragi", str(j.dorsal), ip="5.0.0.99").status_code == 200


def test_la_tabla_de_intentos_no_guarda_motes_ni_ips_en_claro(client):
    login(client, "Fantasma", "1", ip="6.6.6.6")
    for registro in IntentoAcceso.query.all():
        assert "Fantasma" not in registro.clave and "6.6.6.6" not in registro.clave


# ------------------------------------------------------------ sesión
def test_sin_token_o_con_token_falso_da_401(client):
    assert client.get("/api/yo").status_code == 401
    assert client.get("/api/yo", headers={"Authorization": "Bearer inventado"}).status_code == 401


def test_token_caducado_da_401(client, app, nuevo):
    j = nuevo("Feragi")
    app.config["TOKEN_DIAS"] = -1
    assert client.get("/api/yo", headers=j.headers).status_code == 401


def test_token_de_usuario_borrado_no_vale(client, nuevo):
    j = nuevo("Feragi")
    assert client.delete("/api/yo", json={"confirmar": True}, headers=j.headers).status_code == 204
    assert client.get("/api/yo", headers=j.headers).status_code == 401


def test_pendiente_solo_puede_ver_su_estado(client, admin):
    datos = registrar(client, "Nuevo").get_json()
    h = {"Authorization": f"Bearer {datos['token']}"}
    assert client.get("/api/yo", headers=h).get_json()["usuario"]["estado"] == "pendiente"
    assert client.get("/api/jugadores", headers=h).status_code == 403
    assert client.get("/api/clasificacion", headers=h).status_code == 403
    assert client.get("/api/partidos/proximo", headers=h).status_code == 403
    # Tras la aprobación del admin, ya puede
    client.post(f"/api/admin/usuarios/{datos['usuario']['id']}/aprobar", headers=admin.headers)
    assert client.get("/api/jugadores", headers=h).status_code == 200


def test_create_admin_por_cli(app):
    runner = app.test_cli_runner()
    r = runner.invoke(args=["create-admin", "--mote", "Fran", "--nombre-real", ""])
    assert r.exit_code == 0, r.output
    assert "01" in r.output
    u = User.query.filter_by(mote="Fran").one()
    assert (u.rol, u.estado, u.dorsal) == ("admin", "aprobado", 1)
    # Un segundo admin por CLI no se permite
    r2 = runner.invoke(args=["create-admin", "--mote", "Otro", "--nombre-real", ""])
    assert r2.exit_code != 0
