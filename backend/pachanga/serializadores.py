"""Convierte modelos en diccionarios para las respuestas JSON.

REGLA DE PRIVACIDAD: ninguna función de aquí incluye el PIN (ni su hash) ni valoraciones.
El PIN solo sale al registrarse (al propio usuario) y cuando un admin genera uno nuevo.
Los tests de privacidad lo comprueban.
"""
from .models import EQUIPO_BLANCO, EQUIPO_NEGRO

NOMBRES_EQUIPO = {EQUIPO_BLANCO: "Nevados C.F.", EQUIPO_NEGRO: "Sombras F.C."}


def usuario_publico(u):
    return {"id": u.id, "mote": u.mote, "nombre_real": u.nombre_real, "dorsal": u.dorsal,
            "es_admin": u.es_admin}


def usuario_propio(u):
    """Lo que ve cada uno de sí mismo."""
    return {**usuario_publico(u), "rol": u.rol, "estado": u.estado}


def usuario_admin(u):
    """Lo que ve un admin en su panel."""
    return {**usuario_propio(u), "fecha_alta": u.fecha_alta.isoformat(timespec="seconds") + "Z"}


def fecha_partido(fecha):
    return fecha.isoformat(timespec="minutes")


def partido_resumen(p, usuario):
    mio = next((mp for mp in p.jugadores if mp.user_id == usuario.id), None)
    return {
        "id": p.id,
        "fecha": fecha_partido(p.fecha),
        "lugar": p.lugar,
        "estado": p.estado,
        "equipos_generados": p.equipos_generados,
        # null mientras el partido está abierto
        "resultado": ({"blanco": p.goles_blanco, "negro": p.goles_negro}
                      if p.goles_blanco is not None else None),
        "num_convocados": len(p.jugadores),
        "convocado": mio is not None,
        "mi_equipo": mio.equipo if mio else None,
    }


def partido_detalle(p, usuario):
    datos = partido_resumen(p, usuario)
    convocados = sorted(p.jugadores, key=lambda mp: mp.usuario.mote.casefold())
    datos["convocados"] = [{**usuario_publico(mp.usuario), "equipo": mp.equipo} for mp in convocados]
    datos["equipos"] = None
    if p.equipos_generados:
        def equipo(color, fuerza):
            return {
                "color": color,
                "nombre": NOMBRES_EQUIPO[color],
                "fuerza": round(fuerza, 1),
                "jugadores": [usuario_publico(mp.usuario) for mp in convocados if mp.equipo == color],
            }
        datos["equipos"] = {
            "blanco": equipo(EQUIPO_BLANCO, p.fuerza_blanco),
            "negro": equipo(EQUIPO_NEGRO, p.fuerza_negro),
            "diferencia": round(abs(p.fuerza_blanco - p.fuerza_negro), 1),
        }
    return datos


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
