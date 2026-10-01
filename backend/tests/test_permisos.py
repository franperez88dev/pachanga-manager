"""Un jugador (o alguien sin sesión) no puede hacer nada de admin ni tocar datos ajenos."""
import io

import pytest

from test_avatares import PNG_MINIMO

# (método, ruta) de TODAS las acciones de admin. {pid}, {uid} y {rid} se rellenan en el test.
ACCIONES_ADMIN = [
    ("get", "/api/admin/altas"),
    ("post", "/api/admin/usuarios/{uid}/aprobar"),
    ("post", "/api/admin/usuarios/{uid}/rechazar"),
    ("get", "/api/admin/usuarios"),
    ("put", "/api/admin/usuarios/{uid}/rol"),
    ("post", "/api/admin/usuarios/{uid}/pin"),
    ("get", "/api/admin/reportes"),
    ("post", "/api/admin/reportes/{rid}/confirmar"),
    ("post", "/api/admin/reportes/{rid}/descartar"),
    ("post", "/api/partidos"),
    ("patch", "/api/partidos/{pid}"),
    ("delete", "/api/partidos/{pid}"),
    ("put", "/api/partidos/{pid}/convocatoria"),
    ("post", "/api/partidos/{pid}/equipos"),
    ("delete", "/api/partidos/{pid}/equipos"),
    ("post", "/api/partidos/{pid}/cerrar"),
    ("put", "/api/partidos/{pid}/resultado"),
    ("get", "/api/partidos/{pid}/estadisticas"),
    ("put", "/api/partidos/{pid}/estadisticas"),
    ("post", "/api/admin/avatares"),
    ("delete", "/api/admin/avatares/{aid}"),
]


def test_la_lista_incluye_todas_las_rutas_de_admin(app):
    """Si alguien añade un endpoint de admin y no lo mete en ACCIONES_ADMIN, este test falla."""
    en_la_app = set()
    for regla in app.url_map.iter_rules():
        if getattr(app.view_functions[regla.endpoint], "solo_admin", False):
            for metodo in regla.methods - {"HEAD", "OPTIONS"}:
                ruta = regla.rule.replace("<int:pid>", "{pid}").replace("<int:uid>", "{uid}")
                ruta = ruta.replace("<int:rid>", "{rid}").replace("<int:aid>", "{aid}")
                en_la_app.add((metodo.lower(), ruta))
    assert en_la_app == set(ACCIONES_ADMIN)


@pytest.fixture
def escenario(client, admin, plantilla, partido_cerrado):
    """Un partido cerrado y un reporte pendiente de un convocado."""
    pid = partido_cerrado
    autor = plantilla[0]
    r = client.post(f"/api/partidos/{pid}/reportes", json={"goles": 2, "asistencias": 1}, headers=autor.headers)
    assert r.status_code == 201
    a = client.post("/api/admin/avatares", data={"nombre": "Bicho", "imagen": (io.BytesIO(PNG_MINIMO), "b.png")},
                    headers=admin.headers)
    assert a.status_code == 201
    aid = a.get_json()["avatar"]["imagen"].rsplit("/", 1)[1]
    return {"pid": pid, "uid": plantilla[1].id, "rid": r.get_json()["reporte"]["id"], "aid": aid}


@pytest.mark.parametrize("metodo,ruta", ACCIONES_ADMIN)
def test_jugador_recibe_403_en_acciones_de_admin(client, plantilla, escenario, metodo, ruta):
    jugador = plantilla[5]
    r = getattr(client, metodo)(ruta.format(**escenario), json={"rol": "admin"}, headers=jugador.headers)
    assert r.status_code == 403, f"{metodo.upper()} {ruta} debería estar prohibido"


@pytest.mark.parametrize("metodo,ruta", ACCIONES_ADMIN)
def test_sin_sesion_recibe_401_en_acciones_de_admin(client, escenario, metodo, ruta):
    r = getattr(client, metodo)(ruta.format(**escenario), json={})
    assert r.status_code == 401


def test_admin_pendiente_de_aprobacion_no_es_admin(client, nuevo):
    """Aunque alguien tuviera rol admin, sin estar aprobado no puede actuar como tal."""
    raro = nuevo("Raro", admin=True, estado="pendiente")
    assert client.get("/api/admin/altas", headers=raro.headers).status_code == 403


def test_jugador_no_puede_anular_reporte_ajeno(client, plantilla, escenario):
    otro = plantilla[1]
    r = client.post(f"/api/reportes/{escenario['rid']}/anular", headers=otro.headers)
    assert r.status_code == 404


def test_solo_convocados_reportan_goles(client, plantilla, escenario):
    no_convocado = plantilla[11]
    r = client.post(f"/api/partidos/{escenario['pid']}/reportes", json={"goles": 1, "asistencias": 0},
                    headers=no_convocado.headers)
    assert r.status_code == 403


def test_siempre_queda_al_menos_un_admin(client, admin, nuevo):
    r = client.put(f"/api/admin/usuarios/{admin.id}/rol", json={"rol": "jugador"}, headers=admin.headers)
    assert r.status_code == 409
    # Con otro admin, sí puede degradarse
    otro = nuevo("Dani")
    client.put(f"/api/admin/usuarios/{otro.id}/rol", json={"rol": "admin"}, headers=admin.headers)
    r = client.put(f"/api/admin/usuarios/{admin.id}/rol", json={"rol": "jugador"}, headers=admin.headers)
    assert r.status_code == 200
    # Y en cuanto deja de ser admin, pierde el acceso al panel (sin volver a entrar)
    assert client.get("/api/admin/altas", headers=admin.headers).status_code == 403


def test_unico_admin_no_puede_borrar_su_cuenta(client, admin):
    r = client.delete("/api/yo", json={"confirmar": True}, headers=admin.headers)
    assert r.status_code == 409
