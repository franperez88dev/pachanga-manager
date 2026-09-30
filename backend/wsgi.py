"""Punto de entrada para gunicorn en producción: `gunicorn wsgi:app`."""
from pachanga import create_app

app = create_app()
