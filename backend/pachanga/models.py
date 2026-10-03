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

MULTA_PENDIENTE = "pendiente"
MULTA_PAGADA = "pagada"
MULTA_PERDONADA = "perdonada"

PLAZAS = 10  # jugadores por partido (5 contra 5); los que se apunten después son reservas


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
    avatar = db.Column(db.JSON, nullable=False)  # ver avatares.py
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
    # Repartos hechos con estos 10 jugadores (el inicial + los rebarajados por votación)
    num_repartos = db.Column(db.Integer, nullable=False, default=0)
    # Fuerza total de cada equipo en el momento de crearlos (lo único que se enseña)
    fuerza_blanco = db.Column(db.Float)
    fuerza_negro = db.Column(db.Float)
    # Resultado final: lo pone el admin al cerrar el partido
    goles_blanco = db.Column(db.Integer)
    goles_negro = db.Column(db.Integer)
    creado = db.Column(db.DateTime, nullable=False, default=ahora)
    # Precio: "Pagar a <pago_a> (<precio_anticipado> € anticipado | <precio_dia> € el día del partido)".
    # Los precios se guardan en céntimos (220 = 2,20 €) para no tener líos con los decimales.
    pago_a = db.Column(db.String(30))
    precio_anticipado = db.Column(db.Integer)
    precio_dia = db.Column(db.Integer)
    # Texto libre de la primera versión del precio. Solo se enseña si el partido no tiene `pago_a`.
    info_pago = db.Column(db.String(200))

    # Todos los apuntados (titulares y reservas). Usa `titulares` y `reservas` para distinguirlos.
    jugadores = db.relationship("MatchPlayer", back_populates="partido", cascade="all, delete-orphan")

    @property
    def apuntados(self):
        """Todos, por orden de llegada: el que antes reservó hueco, antes va."""
        return sorted(self.jugadores, key=lambda mp: (mp.apuntado or datetime.max, mp.user_id))

    @property
    def titulares(self):
        """Los que juegan. Con los equipos hechos, los que tienen equipo; antes, los 10 primeros."""
        if self.equipos_generados:
            return [mp for mp in self.apuntados if mp.equipo]
        return self.apuntados[:PLAZAS]

    @property
    def reservas(self):
        juegan = {mp.user_id for mp in self.titulares}
        return [mp for mp in self.apuntados if mp.user_id not in juegan]

    @property
    def abierto(self):
        return self.estado == PARTIDO_ABIERTO


class MatchPlayer(db.Model):
    __tablename__ = "convocados"

    match_id = db.Column(db.Integer, db.ForeignKey("partidos.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), primary_key=True)
    # Cuándo reservó su hueco (UTC): decide el orden y, por tanto, quién juega y quién es reserva
    apuntado = db.Column(db.DateTime, nullable=False, default=ahora)
    equipo = db.Column(db.String(10))  # blanco / negro / None (sin equipos todavía, o reserva)
    # Sitio en el campo dentro de su equipo: 0 portero, 1-2 defensas, 3-4 delanteros
    posicion = db.Column(db.Integer)
    # Turno en la portería (cambian cada 5 minutos): 1 = el que empieza de portero
    orden_porteria = db.Column(db.Integer)

    partido = db.relationship("Match", back_populates="jugadores")
    usuario = db.relationship("User")


class VotoRebarajar(db.Model):
    """"¿Deseas una nueva selección de equipo?". Un voto por jugador y por reparto,
    sin poder cambiarlo (la `ronda` es el número de reparto al que se refiere el voto)."""
    __tablename__ = "votos_rebarajar"

    match_id = db.Column(db.Integer, db.ForeignKey("partidos.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), primary_key=True)
    ronda = db.Column(db.Integer, primary_key=True)
    cambiar = db.Column(db.Boolean, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=ahora)


class Multa(db.Model):
    """Multa por liberar el hueco con menos de 24 horas (o porque el admin la pone al quitar a
    alguien). El admin le pone el importe (y lo va subiendo si pasan los días sin pagar) y al
    final la marca como pagada o la perdona. El jugador puede avisar de que ya la ha pagado."""
    __tablename__ = "multas"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True)
    match_id = db.Column(db.Integer, db.ForeignKey("partidos.id"), nullable=False, index=True)
    motivo = db.Column(db.String(120), nullable=False)
    estado = db.Column(db.String(10), nullable=False, default=MULTA_PENDIENTE)
    fecha = db.Column(db.DateTime, nullable=False, default=ahora)
    importe_centimos = db.Column(db.Integer, nullable=False, default=0)
    # Cuándo dijo el jugador "ya la he pagado" (None = no ha dicho nada). Quien confirma es el admin.
    aviso_pago = db.Column(db.DateTime)

    usuario = db.relationship("User")
    partido = db.relationship("Match")


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
