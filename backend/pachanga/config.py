"""Configuración leída de variables de entorno (en local, del archivo .env)."""
import os


def _entero(nombre, defecto):
    return int(os.environ.get(nombre, defecto))


def _booleano(nombre, defecto="0"):
    return os.environ.get(nombre, defecto).strip().lower() in ("1", "true", "si", "sí", "yes")


# Orígenes que usa la app durante el desarrollo: Vite (http://localhost:5173)
# o el navegador contra 127.0.0.1. Son expresiones regulares para cualquier puerto.
ORIGENES_DESARROLLO = [r"http://localhost(:\d+)?", r"http://127\.0\.0\.1(:\d+)?"]


def cargar_config():
    """Devuelve la configuración como diccionario. Se llama al crear la app,
    no al importar el módulo, para que el .env ya esté cargado."""
    # CORS: permiso para que una web de OTRO origen llame a la API. En producción no hace falta
    # (la web y la API están en el mismo servidor); en tu PC sí, porque Vite sirve la web en el
    # puerto 5173 y la API está en el 5000.
    origenes = [o.strip() for o in os.environ.get("CORS_ORIGENES", "").split(",") if o.strip()]
    if _booleano("CORS_DESARROLLO"):
        origenes += ORIGENES_DESARROLLO

    return {
        "SECRET_KEY": os.environ.get("SECRET_KEY"),
        # SQLite: un archivo, backend/instance/pachanga.db (Flask-SQLAlchemy pone la ruta relativa
        # en la carpeta "instance"). Sirve igual en tu PC y en PythonAnywhere, donde el disco no se borra.
        "SQLALCHEMY_DATABASE_URI": os.environ.get("DATABASE_URL", "sqlite:///pachanga.db"),
        "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True},
        # Carpeta con la app web compilada (la crea "npm run build" en app/)
        "CARPETA_WEB": os.environ.get("CARPETA_WEB", os.path.join(os.path.dirname(__file__), "web")),
        # Tamaño máximo de cualquier petición (la API solo recibe JSON pequeños)
        "MAX_CONTENT_LENGTH": 1024 * 1024,
        "CORS_ORIGENES": origenes,
        # En PythonAnywhere las peticiones llegan a través de su proxy: con esto a 1 se lee la IP
        # real del móvil (cabecera X-Forwarded-For). Si no, todos compartirían la IP del proxy y
        # el bloqueo de intentos por IP bloquearía a toda la peña a la vez.
        "CONFIAR_EN_PROXY": _booleano("CONFIAR_EN_PROXY"),

        # Solo en tu PC: permite los comandos de prueba (flask datos-demo, flask demo-votar)
        "PERMITIR_DATOS_DEMO": _booleano("PERMITIR_DATOS_DEMO"),

        # --- Sesión y PIN ---
        "TOKEN_DIAS": _entero("TOKEN_DIAS", 90),
        # Algoritmo del hash del PIN (scrypt: lento a propósito). Los tests usan uno rápido.
        "PIN_HASH_METODO": os.environ.get("PIN_HASH_METODO", "scrypt"),

        # --- Bloqueo de login (ver seguridad.py) ---
        "LOGIN_MAX_INTENTOS_MOTE": _entero("LOGIN_MAX_INTENTOS_MOTE", 5),
        # Más margen por IP: varios colegas pueden compartir la WiFi del bar
        "LOGIN_MAX_INTENTOS_IP": _entero("LOGIN_MAX_INTENTOS_IP", 10),
        "LOGIN_BLOQUEO_MINUTOS": _entero("LOGIN_BLOQUEO_MINUTOS", 15),
        "REGISTRO_MAX_POR_IP_HORA": _entero("REGISTRO_MAX_POR_IP_HORA", 5),

        # --- Huecos y multas ---
        # Zona horaria en la que el admin escribe la fecha de los partidos
        "ZONA_HORARIA": os.environ.get("ZONA_HORARIA", "Europe/Madrid"),
        # Liberar el hueco con menos de estas horas para el partido lleva multa
        "HORAS_SIN_MULTA": _entero("HORAS_SIN_MULTA", 24),

        # --- Equipos (ver equipos.py) ---
        "TOLERANCIA_REBARAJAR": float(os.environ.get("TOLERANCIA_REBARAJAR", "0.5")),
        # Votos "sí" (de los 10 que juegan) para poder rebarajar: con 6 ya son mayoría frente a 4
        "VOTOS_PARA_REBARAJAR": _entero("VOTOS_PARA_REBARAJAR", 6),
        # Repartos máximos por partido: el inicial + 2 cambios
        "MAX_REPARTOS": _entero("MAX_REPARTOS", 3),
    }
