"""Configuración leída de variables de entorno (en local, del archivo .env)."""
import os


def _entero(nombre, defecto):
    return int(os.environ.get(nombre, defecto))


def _booleano(nombre, defecto="0"):
    return os.environ.get(nombre, defecto).strip().lower() in ("1", "true", "si", "sí", "yes")


def normalizar_url_bd(url):
    """Los hostings suelen dar 'postgres://...'; SQLAlchemy necesita el driver explícito."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


# Orígenes que usa la app durante el desarrollo: Vite (http://localhost:5173)
# o el navegador contra 127.0.0.1. Son expresiones regulares para cualquier puerto.
ORIGENES_DESARROLLO = [r"http://localhost(:\d+)?", r"http://127\.0\.0\.1(:\d+)?"]


def cargar_config():
    """Devuelve la configuración como diccionario. Se llama al crear la app,
    no al importar el módulo, para que el .env ya esté cargado."""
    origenes = [o.strip() for o in os.environ.get("CORS_ORIGENES", "https://localhost").split(",") if o.strip()]
    if _booleano("CORS_DESARROLLO"):
        origenes += ORIGENES_DESARROLLO

    return {
        "SECRET_KEY": os.environ.get("SECRET_KEY"),
        # SQLite relativo: Flask-SQLAlchemy lo guarda en backend/instance/
        "SQLALCHEMY_DATABASE_URI": normalizar_url_bd(os.environ.get("DATABASE_URL", "sqlite:///pachanga.db")),
        "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True},
        "CORS_ORIGENES": origenes,
        # Detrás del proxy del hosting, la IP real del cliente llega en X-Forwarded-For
        "CONFIAR_EN_PROXY": _booleano("CONFIAR_EN_PROXY"),

        # --- Sesión ---
        "TOKEN_DIAS": _entero("TOKEN_DIAS", 90),

        # --- Bloqueo de login (ver seguridad.py) ---
        "LOGIN_MAX_INTENTOS_MOTE": _entero("LOGIN_MAX_INTENTOS_MOTE", 5),
        # Más margen por IP: varios colegas pueden compartir la WiFi del bar
        "LOGIN_MAX_INTENTOS_IP": _entero("LOGIN_MAX_INTENTOS_IP", 10),
        "LOGIN_BLOQUEO_MINUTOS": _entero("LOGIN_BLOQUEO_MINUTOS", 15),
        "REGISTRO_MAX_POR_IP_HORA": _entero("REGISTRO_MAX_POR_IP_HORA", 5),

        # --- Equipos (ver equipos.py) ---
        "TOLERANCIA_REBARAJAR": float(os.environ.get("TOLERANCIA_REBARAJAR", "0.5")),
    }
