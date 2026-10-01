"""Comandos de prueba (solo en local)."""
from pachanga.cli import MOTES_DEMO, PIN_DEMO
from pachanga.models import Rating, User, VotoRebarajar


def test_datos_demo_crea_jugadores_con_pin_conocido(app, client):
    r = app.test_cli_runner().invoke(args=["datos-demo"])
    assert r.exit_code == 0, r.output
    assert User.query.count() == len(MOTES_DEMO)
    assert Rating.query.count() == len(MOTES_DEMO) * (len(MOTES_DEMO) - 1)
    login = client.post("/api/auth/login", json={"mote": "Feragi", "pin": PIN_DEMO})
    assert login.status_code == 200
    # Repetirlo no duplica nada
    app.test_cli_runner().invoke(args=["datos-demo"])
    assert User.query.count() == len(MOTES_DEMO)


def test_demo_votar(app, client, admin):
    app.test_cli_runner().invoke(args=["datos-demo"])
    ids = [u.id for u in User.query.filter(User.mote.in_(MOTES_DEMO)).limit(10)]
    pid = client.post("/api/partidos", json={"fecha": "2026-10-04T19:00", "lugar": "Pista"},
                      headers=admin.headers).get_json()["partido"]["id"]
    client.put(f"/api/partidos/{pid}/convocatoria", json={"jugadores": ids}, headers=admin.headers)
    client.post(f"/api/partidos/{pid}/equipos", json={}, headers=admin.headers)
    r = app.test_cli_runner().invoke(args=["demo-votar", str(pid), "--si", "5", "--no", "2"])
    assert r.exit_code == 0, r.output
    assert VotoRebarajar.query.filter_by(cambiar=True).count() == 5
    assert VotoRebarajar.query.filter_by(cambiar=False).count() == 2


def test_comandos_demo_se_niegan_fuera_de_sqlite(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg://x@y/z"
    r = app.test_cli_runner().invoke(args=["datos-demo"])
    assert r.exit_code != 0 and "solo para pruebas" in r.output
