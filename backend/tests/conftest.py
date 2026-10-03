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
        "PIN_HASH_METODO": "pbkdf2:sha256:1000",  # hash rápido: en los tests no hace falta que sea lento
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

    def __init__(self, usuario, pin):
        self.id = usuario.id
        self.mote = usuario.mote
        self.dorsal = usuario.dorsal
        self.pin = pin
        self.headers = {"Authorization": f"Bearer {crear_token(usuario)}"}


@pytest.fixture
def nuevo(app):
    """nuevo("Kike") crea un jugador aprobado; nuevo("Fran", admin=True) un admin."""
    def _crear(mote, admin=False, estado=ESTADO_APROBADO):
        u, pin = crear_usuario(mote, rol=ROL_ADMIN if admin else ROL_JUGADOR, estado=estado)
        db.session.commit()
        return Jugador(u, pin)
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


# Una fecha lejana: así en los tests normales nunca "faltan menos de 24 horas" (no hay multas)
FECHA_LEJANA = "2040-06-02T19:00"


@pytest.fixture
def apuntar(client):
    """apuntar(pid, jugadores): cada jugador reserva su hueco, en ese orden."""
    def _apuntar(pid, jugadores):
        for j in jugadores:
            r = client.post(f"/api/partidos/{pid}/hueco", headers=j.headers)
            assert r.status_code == 201, r.get_json()
        return r.get_json()["partido"]
    return _apuntar


@pytest.fixture
def partido_abierto(client, admin):
    """Partido recién creado, sin nadie apuntado. Devuelve su id."""
    r = client.post("/api/partidos", json={"fecha": FECHA_LEJANA, "lugar": "Polideportivo"},
                    headers=admin.headers)
    return r.get_json()["partido"]["id"]


@pytest.fixture
def partido_con_equipos(client, admin, plantilla, partido_abierto, apuntar):
    """Partido abierto con 10 apuntados (los 10 primeros de la plantilla) y equipos hechos."""
    pid = partido_abierto
    apuntar(pid, plantilla[:10])
    assert client.post(f"/api/partidos/{pid}/equipos", json={}, headers=admin.headers).status_code == 200
    return pid


@pytest.fixture
def partido_cerrado(client, admin, partido_con_equipos):
    """El mismo partido, ya jugado y cerrado con un 3-2."""
    r = client.post(f"/api/partidos/{partido_con_equipos}/cerrar", json={"goles_blanco": 3, "goles_negro": 2},
                    headers=admin.headers)
    assert r.status_code == 200
    return partido_con_equipos