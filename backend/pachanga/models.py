"""Modelos de la base de datos.

Las fechas "técnicas" (altas, intentos de login...) se guardan en UTC sin zona.
La fecha de un partido se guarda tal cual la escribe el admin (hora de España).
"""
from datetime import datetime, timezone

from .extensions import db

ROL_ADMIN = "admin"
ROL_JUGADOR = "jugador"

ESTADO_PENDIENTE = "pendiente"
ESTADO_APROBADO = "aprobado"
# (un alta rechazada se borra: así su mote y su dorsal quedan libres)

PARTIDO_ABIERTO = "abierto"
PARTIDO_CERRADO = "cerrado"

EQUIPO_BLANCO = "blanco"
EQUIPO_NEGRO = "negro"

REPORTE_PENDIENTE = "pendiente"
REPORTE_CONFIRMADO = "confirmado"
REPORTE_DESCARTADO = "descartado"
REPORTE_ANULADO = "anulado"
REPORTES_ACTIVOS = (REPORTE_PENDIENTE, REPORTE_CONFIRMADO)


def ahora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = "usuarios"  # "user" es palabra reservada en PostgreSQL

    id = db.Column(db.Integer, primary_key=True)
    mote = db.Column(db.String(20), nullable=False)
    # Mote en minúsculas: la restricción UNIQUE va aquí para no distinguir mayúsculas
    mote_normalizado = db.Column(db.String(20), nullable=False, unique=True, index=True)
    nombre_real = db.Column(db.String(60))
    # Dorsal público (el número de la camiseta). Al borrar una cuenta queda libre y se reutiliza.
    dorsal = db.Column(db.Integer, nullable=False, unique=True)
    # La clave para entrar es un PIN de 4 cifras. Solo guardamos su hash, nunca el PIN.
    pin_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(10), nullable=False, default=ROL_JUGADOR)
    estado = db.Column(db.String(10), nullable=False, default=ESTADO_PENDIENTE)
    fecha_alta = db.Column(db.DateTime, nullable=False, default=ahora)
    # Al subirlo, todos los tokens antiguos de este usuario dejan de valer
    version_token = db.Column(db.Integer, nullable=False, default=0)

    @property
    def es_admin(self):
        return self.rol == ROL_ADMIN

    @property
    def aprobado(self):
        return self.estado == ESTADO_APROBADO


class Match(db.Model):
    __tablename__ = "partidos"

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False)
    lugar = db.Column(db.String(80), nullable=False)
    estado = db.Column(db.String(10), nullable=False, default=PARTIDO_ABIERTO)
    equipos_generados = db.Column(db.Boolean, nullable=False, default=False)
    # Fuerza total de cada equipo en el momento de crearlos (lo único que se enseña)
    fuerza_blanco = db.Column(db.Float)
    fuerza_negro = db.Column(db.Float)
    # Resultado final: lo pone el admin al cerrar el partido
    goles_blanco = db.Column(db.Integer)
    goles_negro = db.Column(db.Integer)
    creado = db.Column(db.DateTime, nullable=False, default=ahora)

    jugadores = db.relationship("MatchPlayer", back_populates="partido", cascade="all, delete-orphan")

    @property
    def abierto(self):
        return self.estado == PARTIDO_ABIERTO


class MatchPlayer(db.Model):
    __tablename__ = "convocados"

    match_id = db.Column(db.Integer, db.ForeignKey("partidos.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), primary_key=True)
    equipo = db.Column(db.String(10))  # blanco / negro / None si aún no hay equipos

    partido = db.relationship("Match", back_populates="jugadores")
    usuario = db.relationship("User")


class Rating(db.Model):
    __tablename__ = "valoraciones"
    __table_args__ = (
        db.UniqueConstraint("rater_id", "rated_id", name="uq_valoracion_una_vez"),
        db.CheckConstraint("stars BETWEEN 1 AND 5", name="ck_estrellas_1_5"),
        db.CheckConstraint("rater_id <> rated_id", name="ck_no_autovaloracion"),
    )

    id = db.Column(db.Integer, primary_key=True)
    rater_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    rated_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True)
    stars = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=ahora)


class StatReport(db.Model):
    __tablename__ = "reportes"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("partidos.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True)
    goles = db.Column(db.Integer, nullable=False, default=0)
    gpp = db.Column(db.Integer, nullable=False, default=0)  # goles en propia puerta: suman al rival
    asistencias = db.Column(db.Integer, nullable=False, default=0)
    estado = db.Column(db.String(12), nullable=False, default=REPORTE_PENDIENTE)
    fecha = db.Column(db.DateTime, nullable=False, default=ahora)

    partido = db.relationship("Match")
    usuario = db.relationship("User")


class IntentoAcceso(db.Model):
    """Contador de intentos para el bloqueo de login y el límite de registros.
    La clave es un hash (de 'mote:xxx' o 'ip:x.x.x.x'): no guardamos IPs en claro."""
    __tablename__ = "intentos_acceso"

    clave = db.Column(db.String(64), primary_key=True)
    intentos = db.Column(db.Integer, nullable=False, default=0)
    ventana_inicio = db.Column(db.DateTime, nullable=False, default=ahora)
    bloqueado_hasta = db.Column(db.DateTime)
