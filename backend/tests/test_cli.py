"""Comandos de prueba (solo en local)."""
from pachanga.cli import MOTES_DEMO, PIN_DEMO
from pachanga.models import Rating, User, VotoRebarajar


def test_datos_demo_crea_jugadores_con_pin_conocido(app, client):
    app.config["PERMITIR_DATOS_DEMO"] = True
    r = app.test_cli_runner().invoke(args=["datos-demo"])
    assert r.exit_code == 0, r.output
    assert User.query.count() == len(MOTES_DEMO)
    assert Rating.query.count() == len(MOTES_DEMO) * (len(MOTES_DEMO) - 1)
    login = client.post("/api/auth/login", json={"mote": "Feragi", "pin": PIN_DEMO})
    assert login.status_code == 200
    # Repetirlo no duplica nada
    app.test_cli_runner().invoke(args=["datos-demo"])
    assert User.query.count() == len(MOTES_DEMO)


def test_demo_apuntar_y_demo_votar(app, client, admin):
    app.config["PERMITIR_DATOS_DEMO"] = True
    app.test_cli_runner().invoke(args=["datos-demo"])
    pid = client.post("/api/partidos", json={"fecha": "2040-06-02T19:00", "lugar": "Pista"},
                      headers=admin.headers).get_json()["partido"]["id"]
    # Se apuntan los 12 de prueba: 10 juegan y 2 quedan de reservas
    r = app.test_cli_runner().invoke(args=["demo-apuntar", str(pid), "--cuantos", "12"])
    assert r.exit_code == 0 and "Hay 12 en la lista" in r.output, r.output
    p = client.get(f"/api/partidos/{pid}", headers=admin.headers).get_json()["partido"]
    assert [j["mote"] for j in p["apuntados"]] == MOTES_DEMO
    assert client.post(f"/api/partidos/{pid}/equipos", json={}, headers=admin.headers).status_code == 200
    r = app.test_cli_runner().invoke(args=["demo-votar", str(pid), "--si", "5", "--no", "2"])
    assert r.exit_code == 0, r.output
    assert VotoRebarajar.query.filter_by(cambiar=True).count() == 5
    assert VotoRebarajar.query.filter_by(cambiar=False).count() == 2
    # Solo votan los 10 que juegan: quedan 3 sin votar, aunque haya 2 reservas más
    r = app.test_cli_runner().invoke(args=["demo-votar", str(pid), "--si", "4"])
    assert r.exit_code != 0 and "Solo quedan 3" in r.output


def test_comandos_demo_desactivados_por_defecto(app):
    """En el servidor de verdad no hay PERMITIR_DATOS_DEMO: los comandos se niegan y no crean nada."""
    for comando in (["datos-demo"], ["demo-apuntar", "1"], ["demo-votar", "1"]):
        r = app.test_cli_runner().invoke(args=comando)
        assert r.exit_code != 0 and "solo para pruebas en tu PC" in r.output
    assert User.query.count() == 0
