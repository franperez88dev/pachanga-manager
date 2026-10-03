"""Punto de entrada del servidor web en producción (PythonAnywhere).

PythonAnywhere no usa `flask run`: importa este archivo y busca una variable llamada
`application`. Como ahí no hay nadie que cargue el .env por nosotros (en tu PC lo hace el
comando `flask`), lo cargamos aquí antes de crear la app.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from pachanga import create_app  # noqa: E402  (tiene que ir después de cargar el .env)

application = create_app()
app = application
