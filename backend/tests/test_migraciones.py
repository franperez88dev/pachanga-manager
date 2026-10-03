"""Al arrancar con una base de datos de una versión anterior, se añaden las columnas nuevas
sin perder ningún dato."""
import sqlite3

from pachanga import create_app
from pachanga.extensions import db
from pachanga.models import Match, Multa
from pachanga.seguridad import crear_token
from pachanga.servicios import crear_usuario

# Las tablas `partidos` y `convocados` tal como eran antes de los huecos, las reservas y las multas
ESQUEMA_ANTIGUO = """
CREATE TABLE partidos (
    id INTEGER NOT NULL PRIMARY KEY, fecha DATETIME NOT NULL, lugar VARCHAR(80) NOT NULL,
    estado VARCHAR(10) NOT NULL, equipos_generados BOOLEAN NOT NULL, num_repartos INTEGER NOT NULL,
    fuerza_blanco FLOAT, fuerza_negro FLOAT, goles_blanco INTEGER, goles_negro INTEGER,
    creado DATETIME NOT NULL);
CREATE TABLE convocados (
    match_id INTEGER NOT NULL, user_id INTEGER NOT NULL, equipo VARCHAR(10), posicion INTEGER,
    orden_porteria INTEGER, PRIMARY KEY (match_id, user_id));
INSERT INTO partidos VALUES (1, '2026-09-20 19:00:00.000000', 'Pista vieja', 'cerrado', 1, 1,
                             15.0, 15.0, 3, 2, '2026-09-15 10:00:00.000000');
INSERT INTO partidos VALUES (2, '2040-06-02 19:00:00.000000', 'Pista nueva', 'abierto', 0, 0,
                             NULL, NULL, NULL, NULL, '2026-10-01 10:00:00.000000');
"""


def columnas(ruta, tabla):
    with sqlite3.connect(ruta) as con:
        return [fila[1] for fila in con.execute(f"PRAGMA table_info({tabla})")]


def test_una_base_de_datos_antigua_se_actualiza_sola_sin_perder_datos(tmp_path):
    ruta = tmp_path / "antigua.db"
    with sqlite3.connect(ruta) as con:
        con.executescript(ESQUEMA_ANTIGUO)
        # Partido 1 (cerrado): jugaron los usuarios 1-10. Partido 2 (abierto): convocados 1-10, sin equipos.
        for uid in range(1, 11):
            con.execute("INSERT INTO convocados VALUES (1, ?, ?, ?, ?)",
                        (uid, "blanco" if uid <= 5 else "negro", (uid - 1) % 5, (uid - 1) % 5 + 1))
            con.execute("INSERT INTO convocados VALUES (2, ?, NULL, NULL, NULL)", (uid,))
    assert "info_pago" not in columnas(ruta, "partidos") and "apuntado" not in columnas(ruta, "convocados")

    config = {"TESTING": True, "SECRET_KEY": "clave-de-test", "PIN_HASH_METODO": "pbkdf2:sha256:1000",
              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{ruta.as_posix()}"}
    app = create_app(config)
    assert "info_pago" in columnas(ruta, "partidos") and "apuntado" in columnas(ruta, "convocados")

    with app.app_context():
        # Los datos siguen ahí y los convocados de antes son "los que juegan", en el mismo orden
        cerrado, abierto = db.session.get(Match, 1), db.session.get(Match, 2)
        assert (cerrado.lugar, cerrado.goles_blanco, cerrado.goles_negro) == ("Pista vieja", 3, 2)
        assert [mp.user_id for mp in abierto.titulares] == list(range(1, 11)) and abierto.reservas == []
        assert all(mp.apuntado == abierto.creado for mp in abierto.jugadores)
        assert Multa.query.count() == 0  # la tabla nueva también se ha creado

        # Y la app funciona con normalidad sobre esa base de datos: el 11º que se apunta es reserva
        usuarios = [crear_usuario(f"Jugador{n}", estado="aprobado")[0] for n in range(1, 12)]
        db.session.commit()
        r = app.test_client().post("/api/partidos/2/hueco",
                                   headers={"Authorization": f"Bearer {crear_token(usuarios[10])}"})
        assert r.status_code == 201 and r.get_json()["partido"]["soy_reserva"] is True
        db.session.remove()
        db.engine.dispose()

    # Arrancar otra vez no rompe nada (no intenta añadir las columnas dos veces)
    otra = create_app(config)
    with otra.app_context():
        assert db.session.get(Match, 2).lugar == "Pista nueva"
        db.session.remove()
        db.engine.dispose()


# La base de datos tal como quedó con la versión 0.2.0: ya tenía multas (sin importe ni aviso)
# y el precio era solo un texto libre
ESQUEMA_0_2_0 = """
CREATE TABLE partidos (
    id INTEGER NOT NULL PRIMARY KEY, fecha DATETIME NOT NULL, lugar VARCHAR(80) NOT NULL,
    estado VARCHAR(10) NOT NULL, equipos_generados BOOLEAN NOT NULL, num_repartos INTEGER NOT NULL,
    fuerza_blanco FLOAT, fuerza_negro FLOAT, goles_blanco INTEGER, goles_negro INTEGER,
    creado DATETIME NOT NULL, info_pago VARCHAR(200));
CREATE TABLE multas (
    id INTEGER NOT NULL PRIMARY KEY, user_id INTEGER NOT NULL, match_id INTEGER NOT NULL,
    motivo VARCHAR(120) NOT NULL, estado VARCHAR(10) NOT NULL, fecha DATETIME NOT NULL);
INSERT INTO partidos VALUES (1, '2040-06-02 19:00:00.000000', 'Pista', 'abierto', 0, 0,
                             NULL, NULL, NULL, NULL, '2026-10-03 10:00:00.000000', 'Pagar a Feragi (2,2 €)');
INSERT INTO multas VALUES (1, 1, 1, 'Hueco liberado tarde', 'pendiente', '2026-10-03 12:00:00.000000');
"""


def test_la_version_0_2_0_se_actualiza_y_conserva_precio_y_multas(tmp_path):
    ruta = tmp_path / "v020.db"
    with sqlite3.connect(ruta) as con:
        con.executescript(ESQUEMA_0_2_0)

    app = create_app({"TESTING": True, "SECRET_KEY": "clave-de-test", "PIN_HASH_METODO": "pbkdf2:sha256:1000",
                      "SQLALCHEMY_DATABASE_URI": f"sqlite:///{ruta.as_posix()}"})
    assert {"pago_a", "precio_anticipado", "precio_dia"} <= set(columnas(ruta, "partidos"))
    assert {"importe_centimos", "aviso_pago"} <= set(columnas(ruta, "multas"))

    with app.app_context():
        from pachanga.servicios import texto_pago
        partido, multa = db.session.get(Match, 1), db.session.get(Multa, 1)
        assert partido.pago_a is None and texto_pago(partido) == "Pagar a Feragi (2,2 €)"  # el texto de antes se sigue viendo
        assert (multa.motivo, multa.estado, multa.importe_centimos, multa.aviso_pago) == (
            "Hueco liberado tarde", "pendiente", 0, None)
        db.session.remove()
        db.engine.dispose()
