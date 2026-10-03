"""Convierte modelos en diccionarios para las respuestas JSON.

REGLA DE PRIVACIDAD: ninguna función de aquí incluye el PIN (ni su hash) ni valoraciones.
El PIN solo sale al registrarse (al propio usuario) y cuando un admin genera uno nuevo.
Los tests de privacidad lo comprueban.
"""
from flask import current_app

from .models import EQUIPO_BLANCO, EQUIPO_NEGRO, PLAZAS, VotoRebarajar
from .servicios import lleva_multa

NOMBRES_EQUIPO = {EQUIPO_BLANCO: "Nevados C.F.", EQUIPO_NEGRO: "Sombras F.C."}
# Formación 1-2-2 de fútbol sala, por el número de posición guardado con cada jugador
POSICIONES = ["portero", "defensa", "defensa", "delantero", "delantero"]


def usuario_publico(u):
    return {"id": u.id, "mote": u.mote, "nombre_real": u.nombre_real, "dorsal": u.dorsal,
            "es_admin": u.es_admin, "avatar": u.avatar}


def usuario_propio(u):
    """Lo que ve cada uno de sí mismo."""
    return {**usuario_publico(u), "rol": u.rol, "estado": u.estado}


def usuario_admin(u):
    """Lo que ve un admin en su panel."""
    return {**usuario_propio(u), "fecha_alta": u.fecha_alta.isoformat(timespec="seconds") + "Z"}


def fecha_partido(fecha):
    return fecha.isoformat(timespec="minutes")


def partido_resumen(p, usuario):
    juegan = p.titulares
    lista = juegan + p.reservas  # por orden: primero los que juegan, luego los reservas
    mio = next((mp for mp in lista if mp.user_id == usuario.id), None)
    juego = mio is not None and mio in juegan
    return {
        "id": p.id,
        "fecha": fecha_partido(p.fecha),
        "lugar": p.lugar,
        "info_pago": p.info_pago,
        "estado": p.estado,
        "equipos_generados": p.equipos_generados,
        # null mientras el partido está abierto
        "resultado": ({"blanco": p.goles_blanco, "negro": p.goles_negro}
                      if p.goles_blanco is not None else None),
        "plazas": PLAZAS,
        "num_apuntados": len(lista),
        "num_reservas": len(lista) - len(juegan),
        # Mi situación en este partido
        "apuntado": mio is not None,
        "mi_puesto": lista.index(mio) + 1 if mio else None,  # 1, 2, 3... (del 11 en adelante, reserva)
        "soy_reserva": mio is not None and not juego,
        "convocado": juego,  # soy de los 10 que juegan
        "mi_equipo": mio.equipo if mio else None,
        # Con los equipos hechos (o el partido cerrado) los jugadores ya no pueden apuntarse ni borrarse
        "lista_cerrada": p.equipos_generados or not p.abierto,
        # ¿Borrarme ahora me costaría una multa? (soy titular y faltan menos de 24 horas)
        "multa_si_libero": juego and p.abierto and not p.equipos_generados and lleva_multa(p),
        # Para avisar en Inicio: juego, hay votación abierta y aún no he votado
        "debo_votar": juego and votacion_pendiente(p, usuario),
    }


def votacion_pendiente(p, usuario):
    if not (p.abierto and p.equipos_generados and p.num_repartos < current_app.config["MAX_REPARTOS"]):
        return False
    return VotoRebarajar.query.filter_by(match_id=p.id, user_id=usuario.id, ronda=p.num_repartos).first() is None


def partido_detalle(p, usuario):
    datos = partido_resumen(p, usuario)
    juegan = p.titulares
    # La lista de apuntados, numerada como en el grupo de WhatsApp: 1-10 juegan, del 11 en adelante reservas
    datos["apuntados"] = [
        {**usuario_publico(mp.usuario), "puesto": puesto, "reserva": mp not in juegan, "equipo": mp.equipo}
        for puesto, mp in enumerate(juegan + p.reservas, start=1)
    ]
    convocados = sorted(juegan, key=lambda mp: mp.usuario.mote.casefold())
    datos["equipos"] = None
    if p.equipos_generados:
        def equipo(color, fuerza):
            # Ordenados por posición: portero, defensa, defensa, delantero, delantero
            suyos = sorted((mp for mp in convocados if mp.equipo == color), key=lambda mp: mp.posicion or 0)
            return {
                "color": color,
                "nombre": NOMBRES_EQUIPO[color],
                "fuerza": round(fuerza, 1),
                "jugadores": [{**usuario_publico(mp.usuario), "posicion": POSICIONES[mp.posicion or 0],
                               "orden_porteria": mp.orden_porteria} for mp in suyos],
                # ids en el orden en que pasan por la portería (cambio cada 5 minutos)
                "porteria": [mp.user_id for mp in sorted(suyos, key=lambda mp: mp.orden_porteria or 0)],
            }
        datos["equipos"] = {
            "blanco": equipo(EQUIPO_BLANCO, p.fuerza_blanco),
            "negro": equipo(EQUIPO_NEGRO, p.fuerza_negro),
            # Con las fuerzas ya redondeadas, para que cuadre con lo que se ve (15,2 - 15,1 = 0,1)
            "diferencia": round(abs(round(p.fuerza_blanco, 1) - round(p.fuerza_negro, 1)), 1),
        }
    datos["votacion"] = votacion(p, usuario) if p.equipos_generados else None
    return datos


def votacion(p, usuario):
    """Estado de "¿Deseas una nueva selección de equipo?" para el reparto actual.
    Solo se dan los totales; quién votó qué no se enseña (salvo tu propio voto)."""
    cfg = current_app.config
    votos = VotoRebarajar.query.filter_by(match_id=p.id, ronda=p.num_repartos).all()
    si = sum(v.cambiar for v in votos)
    mio = next((v.cambiar for v in votos if v.user_id == usuario.id), None)
    abierta = p.abierto and p.num_repartos < cfg["MAX_REPARTOS"]
    return {
        "repartos_hechos": p.num_repartos,
        "repartos_maximos": cfg["MAX_REPARTOS"],
        "abierta": abierta,
        "votos_si": si,
        "votos_no": len(votos) - si,
        "votos_necesarios": cfg["VOTOS_PARA_REBARAJAR"],
        "mi_voto": mio,
        "se_puede_rebarajar": abierta and si >= cfg["VOTOS_PARA_REBARAJAR"],
    }


def reporte(r):
    return {
        "id": r.id,
        "partido": {"id": r.partido.id, "fecha": fecha_partido(r.partido.fecha), "lugar": r.partido.lugar},
        "jugador": usuario_publico(r.usuario),
        "goles": r.goles,
        "gpp": r.gpp,
        "asistencias": r.asistencias,
        "estado": r.estado,
        "fecha": r.fecha.isoformat(timespec="seconds") + "Z",
    }


def multa(m):
    return {
        "id": m.id,
        "jugador": usuario_publico(m.usuario),
        "partido": {"id": m.partido.id, "fecha": fecha_partido(m.partido.fecha), "lugar": m.partido.lugar},
        "motivo": m.motivo,
        "estado": m.estado,
        "fecha": m.fecha.isoformat(timespec="seconds") + "Z",
    }
