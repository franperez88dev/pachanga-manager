"""Partidos: consulta (todos) y gestión: convocatoria, equipos y cierre (solo admin)."""
from datetime import datetime

from flask import Blueprint, current_app, g, jsonify

from ..equipos import JUGADORES_POR_PARTIDO, elegir_reparto
from ..errores import ErrorApi
from ..extensions import db
from ..models import (
    EQUIPO_BLANCO, EQUIPO_NEGRO, PARTIDO_ABIERTO, PARTIDO_CERRADO,
    REPORTE_CONFIRMADO, REPORTE_PENDIENTE, Match, MatchPlayer, StatReport, User,
)
from ..serializadores import partido_detalle, partido_resumen, reporte
from ..seguridad import requiere_admin, requiere_aprobado
from ..servicios import deshacer_equipos, fuerzas_de
from . import cuerpo_json, entero

bp = Blueprint("partidos", __name__, url_prefix="/api/partidos")


def partido_o_404(pid):
    partido = db.session.get(Match, pid)
    if partido is None:
        raise ErrorApi(404, "Partido no encontrado")
    return partido


def exigir_abierto(partido):
    if not partido.abierto:
        raise ErrorApi(409, "El partido está cerrado y ya no se puede modificar")


def hay_reportes_activos(partido):
    return StatReport.query.filter(
        StatReport.match_id == partido.id,
        StatReport.estado.in_([REPORTE_PENDIENTE, REPORTE_CONFIRMADO]),
    ).count() > 0


def leer_fecha_y_lugar(datos, parcial=False):
    """Valida 'fecha' (formato 2026-10-04T19:00) y 'lugar'. Con parcial=True son opcionales."""
    cambios = {}
    if "fecha" in datos or not parcial:
        try:
            cambios["fecha"] = datetime.fromisoformat(str(datos.get("fecha", ""))).replace(tzinfo=None, second=0, microsecond=0)
        except ValueError:
            raise ErrorApi(400, "Fecha no válida. Formato: 2026-10-04T19:00")
    if "lugar" in datos or not parcial:
        lugar = " ".join(str(datos.get("lugar") or "").split())
        if not 1 <= len(lugar) <= 80:
            raise ErrorApi(400, "Escribe el lugar (máximo 80 caracteres)")
        cambios["lugar"] = lugar
    return cambios


# ------------------------------------------------------------ consulta (jugadores)
@bp.get("")
@requiere_aprobado
def lista():
    partidos = Match.query.order_by(Match.fecha.desc()).all()
    return jsonify(partidos=[partido_resumen(p, g.usuario) for p in partidos])


@bp.get("/proximo")
@requiere_aprobado
def proximo():
    """El partido abierto más cercano en fecha (o null si no hay ninguno)."""
    p = Match.query.filter_by(estado=PARTIDO_ABIERTO).order_by(Match.fecha.asc()).first()
    return jsonify(partido=partido_detalle(p, g.usuario) if p else None)


@bp.get("/<int:pid>")
@requiere_aprobado
def detalle(pid):
    return jsonify(partido=partido_detalle(partido_o_404(pid), g.usuario))


# ------------------------------------------------------------ gestión (admin)
@bp.post("")
@requiere_admin
def crear():
    partido = Match(**leer_fecha_y_lugar(cuerpo_json()))
    db.session.add(partido)
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario)), 201


@bp.patch("/<int:pid>")
@requiere_admin
def editar(pid):
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    for campo, valor in leer_fecha_y_lugar(cuerpo_json(), parcial=True).items():
        setattr(partido, campo, valor)
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


@bp.delete("/<int:pid>")
@requiere_admin
def borrar(pid):
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    if hay_reportes_activos(partido):
        raise ErrorApi(409, "Ya hay goles apuntados en este partido; descártalos antes de borrarlo")
    StatReport.query.filter_by(match_id=partido.id).delete(synchronize_session=False)
    db.session.delete(partido)
    db.session.commit()
    return "", 204


@bp.put("/<int:pid>/convocatoria")
@requiere_admin
def convocatoria(pid):
    """Recibe {"jugadores": [ids]} con EXACTAMENTE 10 jugadores aprobados distintos.
    Cambiar la convocatoria deshace los equipos que hubiera."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    ids = cuerpo_json().get("jugadores")
    if not isinstance(ids, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ids):
        raise ErrorApi(400, "'jugadores' debe ser una lista de ids")
    if len(set(ids)) != len(ids) or len(ids) != JUGADORES_POR_PARTIDO:
        raise ErrorApi(400, f"La convocatoria debe tener exactamente {JUGADORES_POR_PARTIDO} jugadores distintos")
    usuarios = User.query.filter(User.id.in_(ids)).all()
    if len(usuarios) != len(ids) or not all(u.aprobado for u in usuarios):
        raise ErrorApi(400, "Todos los convocados deben ser jugadores aprobados")
    if hay_reportes_activos(partido):
        raise ErrorApi(409, "Ya hay goles apuntados en este partido; no se puede cambiar la convocatoria")

    partido.jugadores.clear()
    db.session.flush()
    partido.jugadores.extend(MatchPlayer(user_id=uid) for uid in ids)
    deshacer_equipos(partido)
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


@bp.post("/<int:pid>/equipos")
@requiere_admin
def crear_equipos(pid):
    """{"rebarajar": false} -> el reparto más igualado ("Crear equipos").
    {"rebarajar": true}  -> otro reparto equilibrado distinto del actual."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    if len(partido.jugadores) != JUGADORES_POR_PARTIDO:
        raise ErrorApi(409, f"Primero convoca a {JUGADORES_POR_PARTIDO} jugadores")
    if hay_reportes_activos(partido):
        raise ErrorApi(409, "Ya hay goles apuntados en este partido; no se pueden rehacer los equipos")

    anterior = None
    if cuerpo_json().get("rebarajar") is True and partido.equipos_generados:
        anterior = (
            {mp.user_id for mp in partido.jugadores if mp.equipo == EQUIPO_BLANCO},
            {mp.user_id for mp in partido.jugadores if mp.equipo == EQUIPO_NEGRO},
        )

    fuerzas = fuerzas_de([mp.user_id for mp in partido.jugadores])
    blanco, _negro, f_blanco, f_negro = elegir_reparto(
        fuerzas, anterior=anterior, tolerancia=current_app.config["TOLERANCIA_REBARAJAR"]
    )
    for mp in partido.jugadores:
        mp.equipo = EQUIPO_BLANCO if mp.user_id in blanco else EQUIPO_NEGRO
    partido.equipos_generados = True
    partido.fuerza_blanco = f_blanco
    partido.fuerza_negro = f_negro
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


@bp.delete("/<int:pid>/equipos")
@requiere_admin
def quitar_equipos(pid):
    """Botón "Volver a elegir": se deshacen los equipos y se mantiene la convocatoria."""
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    if hay_reportes_activos(partido):
        raise ErrorApi(409, "Ya hay goles apuntados en este partido; no se pueden deshacer los equipos")
    deshacer_equipos(partido)
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


@bp.post("/<int:pid>/cerrar")
@requiere_admin
def cerrar(pid):
    partido = partido_o_404(pid)
    exigir_abierto(partido)
    if not partido.equipos_generados:
        raise ErrorApi(409, "No se puede cerrar un partido sin equipos")
    partido.estado = PARTIDO_CERRADO
    db.session.commit()
    return jsonify(partido=partido_detalle(partido, g.usuario))


# ------------------------------------------------------------ reportar goles (convocados)
@bp.post("/<int:pid>/reportes")
@requiere_aprobado
def reportar(pid):
    partido = partido_o_404(pid)
    convocado = any(mp.user_id == g.usuario.id for mp in partido.jugadores)
    if not convocado:
        raise ErrorApi(403, "Solo los convocados pueden apuntar goles en este partido")
    if not partido.equipos_generados:
        raise ErrorApi(409, "Todavía no hay equipos para este partido")
    datos = cuerpo_json()
    goles = entero(datos, "goles", 0, 30)
    asistencias = entero(datos, "asistencias", 0, 30)
    if goles == 0 and asistencias == 0:
        raise ErrorApi(400, "Apunta al menos un gol o una asistencia")
    ya = StatReport.query.filter(
        StatReport.match_id == partido.id,
        StatReport.user_id == g.usuario.id,
        StatReport.estado.in_([REPORTE_PENDIENTE, REPORTE_CONFIRMADO]),
    ).first()
    if ya:
        raise ErrorApi(409, "Ya apuntaste tus datos de este partido. Anula el pendiente si te equivocaste")

    r = StatReport(match_id=partido.id, user_id=g.usuario.id, goles=goles, asistencias=asistencias)
    db.session.add(r)
    db.session.commit()
    return jsonify(reporte=reporte(r)), 201
