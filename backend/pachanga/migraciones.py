"""Pone al día una base de datos creada con una versión anterior de la app.

`db.create_all()` crea las TABLAS que falten, pero no toca las que ya existen: si a una
tabla le añadimos una columna en models.py, en una base de datos antigua esa columna no está.
Aquí se añaden esas columnas, sin borrar ni cambiar ningún dato. Se ejecuta al arrancar
la app y se puede repetir las veces que haga falta: si no falta nada, no hace nada.
"""
from sqlalchemy import inspect, text

from .extensions import db

# (tabla, columna, tipo SQL). Las columnas nuevas se añaden vacías (NULL), salvo que el tipo
# diga otra cosa con DEFAULT.
COLUMNAS_NUEVAS = [
    ("partidos", "info_pago", "VARCHAR(200)"),
    ("convocados", "apuntado", "DATETIME"),
    ("partidos", "pago_a", "VARCHAR(30)"),
    ("partidos", "precio_anticipado", "INTEGER"),
    ("partidos", "precio_dia", "INTEGER"),
    ("multas", "importe_centimos", "INTEGER NOT NULL DEFAULT 0"),
    ("multas", "aviso_pago", "DATETIME"),
]


def actualizar_esquema():
    """Devuelve la lista de columnas que ha añadido (vacía si la base de datos ya estaba al día)."""
    inspector = inspect(db.engine)
    añadidas = []
    for tabla, columna, tipo in COLUMNAS_NUEVAS:
        if columna not in {c["name"] for c in inspector.get_columns(tabla)}:
            db.session.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}"))
            añadidas.append(f"{tabla}.{columna}")

    if "convocados.apuntado" in añadidas:
        # Los convocados de antes (los elegía el admin) no tienen hora de apuntarse:
        # les ponemos la de creación de su partido, y así siguen siendo los que juegan.
        db.session.execute(text(
            "UPDATE convocados SET apuntado = "
            "(SELECT creado FROM partidos WHERE partidos.id = convocados.match_id) "
            "WHERE apuntado IS NULL"))
    db.session.commit()
    return añadidas
