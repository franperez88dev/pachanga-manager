"""Tokens de sesión, bloqueo por intentos fallidos y control de permisos."""
import hashlib
import hmac
from datetime import timedelta
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from .errores import ErrorApi
from .extensions import db
from .models import IntentoAcceso, User, ahora

MENSAJE_LOGIN_INCORRECTO = "Mote o dorsal incorrectos"


# ---------------------------------------------------------------- tokens
def _serializador():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="pachanga-sesion")


def crear_token(usuario):
    """Token firmado con el id y la versión de token del usuario.
    No es JWT, pero la idea es la misma: el servidor puede comprobar que no se ha
    manipulado sin guardarlo en la base de datos."""
    return _serializador().dumps({"uid": usuario.id, "v": usuario.version_token})


def usuario_desde_token(token):
    max_segundos = current_app.config["TOKEN_DIAS"] * 24 * 3600
    try:
        datos = _serializador().loads(token, max_age=max_segundos)
    except BadSignature:  # incluye el caso de token caducado (SignatureExpired)
        return None
    usuario = db.session.get(User, datos.get("uid"))
    if usuario is None or usuario.version_token != datos.get("v"):
        return None
    return usuario


# ---------------------------------------------------------------- permisos
def _usuario_de_la_peticion():
    cabecera = request.headers.get("Authorization", "")
    if not cabecera.startswith("Bearer "):
        raise ErrorApi(401, "Inicia sesión para continuar")
    usuario = usuario_desde_token(cabecera[len("Bearer "):].strip())
    if usuario is None:
        raise ErrorApi(401, "Tu sesión ha caducado. Vuelve a entrar")
    return usuario


def requiere_sesion(f):
    """Cualquier usuario con sesión, aunque esté pendiente de aprobación."""
    @wraps(f)
    def envoltura(*args, **kwargs):
        g.usuario = _usuario_de_la_peticion()
        return f(*args, **kwargs)
    return envoltura


def requiere_aprobado(f):
    """Jugador (o admin) con el alta aprobada."""
    @wraps(f)
    def envoltura(*args, **kwargs):
        g.usuario = _usuario_de_la_peticion()
        if not g.usuario.aprobado:
            raise ErrorApi(403, "Tu alta está pendiente de aprobación")
        return f(*args, **kwargs)
    return envoltura


def requiere_admin(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        g.usuario = _usuario_de_la_peticion()
        if not (g.usuario.aprobado and g.usuario.es_admin):
            raise ErrorApi(403, "Solo un admin puede hacer esto")
        return f(*args, **kwargs)
    return envoltura


# ---------------------------------------------------------------- bloqueo de intentos
def clave_intento(tipo, valor):
    """Hash con la clave secreta: en la tabla no quedan motes ni IPs legibles."""
    mensaje = f"{tipo}:{valor}".encode()
    return hmac.new(current_app.config["SECRET_KEY"].encode(), mensaje, hashlib.sha256).hexdigest()


def segundos_bloqueado(clave):
    registro = db.session.get(IntentoAcceso, clave)
    if registro and registro.bloqueado_hasta and registro.bloqueado_hasta > ahora():
        return int((registro.bloqueado_hasta - ahora()).total_seconds()) + 1
    return 0


def sumar_intento(clave, maximo, minutos):
    """Suma un intento dentro de una ventana de `minutos`. Al llegar a `maximo`
    bloquea la clave durante `minutos` y el contador vuelve a cero."""
    momento = ahora()
    ventana = timedelta(minutes=minutos)
    registro = db.session.get(IntentoAcceso, clave)
    if registro is None:
        registro = IntentoAcceso(clave=clave, intentos=0, ventana_inicio=momento)
        db.session.add(registro)
    if momento - registro.ventana_inicio > ventana:
        registro.intentos = 0
        registro.ventana_inicio = momento
    registro.intentos += 1
    if registro.intentos >= maximo:
        registro.bloqueado_hasta = momento + ventana
        registro.intentos = 0
        registro.ventana_inicio = momento


def olvidar_intentos(clave):
    registro = db.session.get(IntentoAcceso, clave)
    if registro:
        db.session.delete(registro)


def limpiar_intentos_viejos():
    """Borra registros caducados para que la tabla no crezca sin fin."""
    limite = ahora() - timedelta(days=1)
    IntentoAcceso.query.filter(
        IntentoAcceso.ventana_inicio < limite,
        db.or_(IntentoAcceso.bloqueado_hasta.is_(None), IntentoAcceso.bloqueado_hasta < ahora()),
    ).delete(synchronize_session=False)


def error_demasiados_intentos(segundos):
    minutos = max(1, round(segundos / 60))
    return ErrorApi(
        429,
        f"Demasiados intentos. Espera {minutos} minuto{'s' if minutos != 1 else ''} y vuelve a probar",
        {"Retry-After": str(segundos)},
    )


def normalizar_mote(mote):
    return " ".join(mote.split()).casefold()


def verificar_credenciales(mote, dorsal_texto):
    """Comprueba mote + dorsal aplicando el bloqueo por mote y por IP.

    - Si el mote no existe o el dorsal no coincide, el error es EXACTAMENTE el mismo.
    - El contador por mote funciona también con motes que no existen, así el bloqueo
      no delata qué motes están registrados.
    - Mientras hay bloqueo ni siquiera se comprueba el dorsal.
    Devuelve el usuario o lanza ErrorApi (401 o 429). Hace commit de los contadores.
    """
    cfg = current_app.config
    clave_mote = clave_intento("mote", normalizar_mote(mote))
    clave_ip = clave_intento("ip", request.remote_addr or "desconocida")

    espera = max(segundos_bloqueado(clave_mote), segundos_bloqueado(clave_ip))
    if espera:
        raise error_demasiados_intentos(espera)

    usuario = User.query.filter_by(mote_normalizado=normalizar_mote(mote)).first()
    dorsal_texto = (dorsal_texto or "").strip()
    correcto = (
        usuario is not None
        and dorsal_texto.isascii()
        and dorsal_texto.isdigit()
        and len(dorsal_texto) <= 6
        and hmac.compare_digest(str(int(dorsal_texto)), str(usuario.dorsal))
    )

    limpiar_intentos_viejos()
    if not correcto:
        sumar_intento(clave_mote, cfg["LOGIN_MAX_INTENTOS_MOTE"], cfg["LOGIN_BLOQUEO_MINUTOS"])
        sumar_intento(clave_ip, cfg["LOGIN_MAX_INTENTOS_IP"], cfg["LOGIN_BLOQUEO_MINUTOS"])
        db.session.commit()
        raise ErrorApi(401, MENSAJE_LOGIN_INCORRECTO)

    # El contador por IP no se limpia al acertar: si no, quien tenga una cuenta
    # podría alternar aciertos y fallos para probar dorsales de otros sin límite.
    olvidar_intentos(clave_mote)
    db.session.commit()
    return usuario
