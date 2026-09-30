"""PIN, tokens de sesión, bloqueo por intentos fallidos y control de permisos."""
import hashlib
import hmac
import secrets
from datetime import timedelta
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from .errores import ErrorApi
from .extensions import db
from .models import IntentoAcceso, User, ahora

MENSAJE_LOGIN_INCORRECTO = "Mote o PIN incorrectos"
CIFRAS_PIN = 4


# ---------------------------------------------------------------- PIN
def nuevo_pin():
    """PIN aleatorio de 4 cifras (puede empezar por 0, p. ej. '0427').
    `secrets` usa el generador seguro del sistema, no el de `random`."""
    return f"{secrets.randbelow(10 ** CIFRAS_PIN):0{CIFRAS_PIN}d}"


def hash_pin(pin):
    # Como con una contraseña: guardamos un hash lento con sal, nunca el PIN en claro
    return generate_password_hash(pin, method=current_app.config["PIN_HASH_METODO"])


def pin_correcto(usuario, pin):
    return check_password_hash(usuario.pin_hash, pin)


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
    envoltura.solo_admin = True  # marca que usan los tests para comprobar que no se olvida ninguna
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


_hash_de_relleno = {}


def _comprobar_pin_de_relleno(pin):
    """Si el mote no existe, comprobamos igualmente un PIN contra un hash cualquiera.
    Así la respuesta tarda lo mismo y no se puede adivinar por el tiempo qué motes existen."""
    metodo = current_app.config["PIN_HASH_METODO"]
    if metodo not in _hash_de_relleno:
        _hash_de_relleno[metodo] = generate_password_hash("relleno", method=metodo)
    check_password_hash(_hash_de_relleno[metodo], pin)


def verificar_credenciales(mote, pin):
    """Comprueba mote + PIN aplicando el bloqueo por mote y por IP.

    - Si el mote no existe o el PIN no coincide, el error es EXACTAMENTE el mismo.
    - El contador por mote funciona también con motes que no existen, así el bloqueo
      no delata qué motes están registrados.
    - Mientras hay bloqueo ni siquiera se comprueba el PIN.
    Devuelve el usuario o lanza ErrorApi (401 o 429). Hace commit de los contadores.
    """
    cfg = current_app.config
    clave_mote = clave_intento("mote", normalizar_mote(mote))
    clave_ip = clave_intento("ip", request.remote_addr or "desconocida")

    espera = max(segundos_bloqueado(clave_mote), segundos_bloqueado(clave_ip))
    if espera:
        raise error_demasiados_intentos(espera)

    usuario = User.query.filter_by(mote_normalizado=normalizar_mote(mote)).first()
    pin = (pin or "").strip()
    formato_ok = len(pin) == CIFRAS_PIN and pin.isascii() and pin.isdigit()
    if usuario is None:
        _comprobar_pin_de_relleno(pin)
        correcto = False
    else:
        correcto = pin_correcto(usuario, pin) and formato_ok

    limpiar_intentos_viejos()
    if not correcto:
        sumar_intento(clave_mote, cfg["LOGIN_MAX_INTENTOS_MOTE"], cfg["LOGIN_BLOQUEO_MINUTOS"])
        sumar_intento(clave_ip, cfg["LOGIN_MAX_INTENTOS_IP"], cfg["LOGIN_BLOQUEO_MINUTOS"])
        db.session.commit()
        raise ErrorApi(401, MENSAJE_LOGIN_INCORRECTO)

    # El contador por IP no se limpia al acertar: si no, quien tenga una cuenta
    # podría alternar aciertos y fallos para probar PINes de otros sin límite.
    olvidar_intentos(clave_mote)
    db.session.commit()
    return usuario
