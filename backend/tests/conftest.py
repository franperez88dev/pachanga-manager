"""Utilidades comunes de los tests. Cada test usa una base de datos SQLite
en memoria nueva, así que los tests no se afectan entre sí."""
import pytest

from pachanga import create_app
from pachanga.extensions import db
from pachanga.models import ESTADO_APROBADO, ROL_ADMIN, ROL_JUGADOR
from pachanga.seguridad import crear_token
from pachanga.servicios import crear_usuario


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "clave-de-test",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
    })
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


class Jugador:
    """Un usuario de prueba con su token listo para usar."""

    def __init__(self, usuario):
        self.id = usuario.id
        self.mote = usuario.mote
        self.dorsal = usuario.dorsal
        self.headers = {"Authorization": f"Bearer {crear_token(usuario)}"}


@pytest.fixture
def nuevo(app):
    """nuevo("Kike") crea un jugador aprobado; nuevo("Fran", admin=True) un admin."""
    def _crear(mote, admin=False, estado=ESTADO_APROBADO):
        u = crear_usuario(mote, rol=ROL_ADMIN if admin else ROL_JUGADOR, estado=estado)
        db.session.commit()
        return Jugador(u)
    return _crear


@pytest.fixture
def admin(nuevo):
    return nuevo("Fran", admin=True)


@pytest.fixture
def plantilla(nuevo):
    """12 jugadores aprobados (además del admin, si se pide aparte)."""
    motes = ["Feragi", "Chuti", "El Tanke", "Rulo", "Kike", "Nino",
             "Josemi", "Payo", "Sergi", "Toni", "Manu", "Guaje"]
    return [nuevo(m) for m in motes]


@pytest.fixture
def partido_con_equipos(client, admin, plantilla):
    """Partido abierto con 10 convocados y equipos hechos. Devuelve su id."""
    r = client.post("/api/partidos", json={"fecha": "2026-10-04T19:00", "lugar": "Polideportivo"},
                    headers=admin.headers)
    pid = r.get_json()["partido"]["id"]
    ids = [j.id for j in plantilla[:10]]
    assert client.put(f"/api/partidos/{pid}/convocatoria", json={"jugadores": ids},
                      headers=admin.headers).status_code == 200
    assert client.post(f"/api/partidos/{pid}/equipos", json={}, headers=admin.headers).status_code == 200
    return pid
