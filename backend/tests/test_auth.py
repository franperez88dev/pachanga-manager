"""Registro, dorsales, login con PIN, bloqueo de intentos y sesión."""
import re
from datetime import timedelta

from pachanga.extensions import db
from pachanga.models import IntentoAcceso, User, ahora
from pachanga.seguridad import MENSAJE_LOGIN_INCORRECTO


def registrar(client, mote, ip="10.0.0.1", **extra):
    return client.post("/api/auth/registro", json={"mote": mote, **extra},
                       environ_base={"REMOTE_ADDR": ip})


def login(client, mote, pin, ip="10.0.0.1"):
    return client.post("/api/auth/login", json={"mote": mote, "pin": pin},
                       environ_base={"REMOTE_ADDR": ip})


def pin_distinto(pin):
    return f"{(int(pin) + 1) % 10000:04d}"


# ------------------------------------------------------------ registro, dorsales y PIN
def test_registro_da_pin_de_4_cifras_dorsal_y_queda_pendiente(client, admin):
    r = registrar(client, "Kike", nombre_real="Enrique")
    assert r.status_code == 201
    datos = r.get_json()
    assert re.fullmatch(r"\d{4}", datos["pin"])
    assert datos["usuario"]["dorsal"] == 2  # el admin es el 1
    assert datos["usuario"]["estado"] == "pendiente"
    assert datos["usuario"]["nombre_real"] == "Enrique"


def test_el_pin_se_guarda_cifrado(client):
    pin = registrar(client, "Kike").get_json()["pin"]
    u = User.query.filter_by(mote="Kike").one()
    assert pin not in u.pin_hash


def test_mote_unico_sin_distinguir_mayusculas(client, admin):
    assert registrar(client, "El Tanke").status_code == 201
    assert registrar(client, "el  TANKE", ip="10.0.0.2").status_code == 409


def test_mote_invalido(client):
    assert registrar(client, "x").status_code == 400
    assert registrar(client, "<script>").status_code == 400
    assert registrar(client, "a" * 21).status_code == 400


def test_dorsal_libre_mas_bajo_se_reutiliza_tras_borrar_cuenta(client, admin, nuevo):
    uno, dos, tres = nuevo("Uno"), nuevo("Dos"), nuevo("Tres")
    assert (uno.dorsal, dos.dorsal, tres.dorsal) == (2, 3, 4)
    client.delete("/api/yo", json={"confirmar": True}, headers=dos.headers)
    assert registrar(client, "Nuevo").get_json()["usuario"]["dorsal"] == 3
    assert registrar(client, "Otro").get_json()["usuario"]["dorsal"] == 5


def test_alta_rechazada_libera_mote_y_dorsal(client, admin):
    datos = registrar(client, "Primo").get_json()
    r = client.post(f"/api/admin/usuarios/{datos['usuario']['id']}/rechazar", headers=admin.headers)
    assert r.status_code == 204
    otra = registrar(client, "Primo")
    assert otra.status_code == 201
    assert otra.get_json()["usuario"]["dorsal"] == datos["usuario"]["dorsal"]


def test_limite_de_registros_por_ip(client, app):
    maximo = app.config["REGISTRO_MAX_POR_IP_HORA"]
    for i in range(maximo):
        assert registrar(client, f"Nuevo{i}", ip="9.9.9.9").status_code == 201
    assert registrar(client, "Otro", ip="9.9.9.9").status_code == 429
    assert registrar(client, "Otro", ip="9.9.9.8").status_code == 201


# ------------------------------------------------------------ login
def test_login_con_mote_y_pin(client, nuevo):
    j = nuevo("Feragi")
    r = login(client, "feragi", j.pin)
    assert r.status_code == 200
    datos = r.get_json()
    assert datos["usuario"]["mote"] == "Feragi"
    assert datos["usuario"]["rol"] == "jugador"
    assert "pin" not in datos["usuario"]
    yo = client.get("/api/yo", headers={"Authorization": f"Bearer {datos['token']}"})
    assert yo.status_code == 200


def test_el_dorsal_ya_no_sirve_para_entrar(client, nuevo):
    j = nuevo("Feragi")
    assert login(client, "Feragi", str(j.dorsal)).status_code == 401


def test_login_sabe_si_eres_admin(client, admin):
    assert login(client, "Fran", admin.pin).get_json()["usuario"]["rol"] == "admin"


def test_error_identico_para_mote_inexistente_y_pin_incorrecto(client, nuevo):
    j = nuevo("Feragi")
    malo_pin = login(client, "Feragi", pin_distinto(j.pin), ip="1.1.1.1")
    no_existe = login(client, "Fantasma", "1234", ip="1.1.1.2")
    assert malo_pin.status_code == no_existe.status_code == 401
    assert malo_pin.get_json() == no_existe.get_json() == {"error": MENSAJE_LOGIN_INCORRECTO}


def test_pin_con_formato_raro_es_login_incorrecto(client, nuevo):
    nuevo("Feragi")
    for pin in ("abcd", "²²²²", "9" * 5000, "12"):
        assert login(client, "Feragi", pin, ip=f"7.7.7.{len(pin) % 250}").status_code == 401


def test_bloqueo_por_mote_tras_varios_fallos(client, app, nuevo):
    j = nuevo("Feragi")
    malo = pin_distinto(j.pin)
    # Cada fallo desde una IP distinta, para probar solo el bloqueo por mote
    for i in range(app.config["LOGIN_MAX_INTENTOS_MOTE"]):
        assert login(client, "Feragi", malo, ip=f"2.0.0.{i}").status_code == 401
    r = login(client, "Feragi", j.pin, ip="2.0.0.200")
    assert r.status_code == 429, "Bloqueado: ni con el PIN correcto se entra"
    assert "Retry-After" in r.headers


def test_bloqueo_por_mote_tambien_con_motes_inexistentes(client, app):
    """Si solo se bloquearan motes existentes, el bloqueo delataría quién está registrado."""
    for i in range(app.config["LOGIN_MAX_INTENTOS_MOTE"]):
        login(client, "Fantasma", "1111", ip=f"3.0.0.{i}")
    assert login(client, "Fantasma", "1111", ip="3.0.0.200").status_code == 429


def test_bloqueo_por_ip_aunque_se_cambie_de_mote(client, app, nuevo):
    j = nuevo("Feragi")
    for i in range(app.config["LOGIN_MAX_INTENTOS_IP"]):
        login(client, f"Mote{i}", "1111", ip="4.4.4.4")
    assert login(client, "Feragi", j.pin, ip="4.4.4.4").status_code == 429
    assert login(client, "Feragi", j.pin, ip="4.4.4.5").status_code == 200


def test_el_bloqueo_caduca(client, app, nuevo):
    j = nuevo("Feragi")
    for i in range(app.config["LOGIN_MAX_INTENTOS_MOTE"]):
        login(client, "Feragi", pin_distinto(j.pin), ip=f"5.0.0.{i}")
    assert login(client, "Feragi", j.pin, ip="5.0.0.99").status_code == 429
    # Simulamos que han pasado los minutos de bloqueo
    for registro in IntentoAcceso.query.all():
        if registro.bloqueado_hasta:
            registro.bloqueado_hasta = ahora() - timedelta(seconds=1)
    db.session.commit()
    assert login(client, "Feragi", j.pin, ip="5.0.0.99").status_code == 200


def test_la_tabla_de_intentos_no_guarda_motes_ni_ips_en_claro(client):
    login(client, "Fantasma", "1111", ip="6.6.6.6")
    for registro in IntentoAcceso.query.all():
        assert "Fantasma" not in registro.clave and "6.6.6.6" not in registro.clave


# ------------------------------------------------------------ PIN olvidado
def test_admin_genera_pin_nuevo_y_se_cierran_las_sesiones_viejas(client, admin, nuevo):
    j = nuevo("Feragi")
    r = client.post(f"/api/admin/usuarios/{j.id}/pin", headers=admin.headers)
    assert r.status_code == 200
    nuevo_pin = r.get_json()["pin"]
    assert client.get("/api/yo", headers=j.headers).status_code == 401  # sesión vieja cerrada
    if nuevo_pin != j.pin:  # (1 entre 10.000 veces el azar repite el mismo)
        assert login(client, "Feragi", j.pin).status_code == 401
    assert login(client, "Feragi", nuevo_pin, ip="8.8.8.8").status_code == 200


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
    client.post(f"/api/admin/usuarios/{datos['usuario']['id']}/aprobar", headers=admin.headers)
    assert client.get("/api/jugadores", headers=h).status_code == 200


def test_create_admin_por_cli(app):
    runner = app.test_cli_runner()
    r = runner.invoke(args=["create-admin", "--mote", "Fran"], input="\n")
    assert r.exit_code == 0, r.output
    u = User.query.filter_by(mote="Fran").one()
    assert (u.rol, u.estado, u.dorsal) == ("admin", "aprobado", 1)
    pin = re.search(r"Tu PIN es: (\d{4})", r.output).group(1)
    with app.test_client() as c:
        assert login(c, "Fran", pin).status_code == 200
    r2 = runner.invoke(args=["create-admin", "--mote", "Otro"], input="\n")
    assert r2.exit_code != 0
