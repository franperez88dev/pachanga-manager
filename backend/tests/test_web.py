"""La app web compilada se sirve desde Flask (misma dirección que la API) y CORS solo en desarrollo."""
import pytest

from pachanga import create_app
from pachanga.config import ORIGENES_DESARROLLO


@pytest.fixture
def web(tmp_path):
    """Una carpeta que imita lo que genera `npm run build`."""
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><title>Pachanga</title>", encoding="utf-8")
    (tmp_path / "assets" / "index-abc123.js").write_text("console.log('hola')", encoding="utf-8")
    (tmp_path / "favicon.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
    (tmp_path / "manifest.webmanifest").write_text("{}", encoding="utf-8")
    (tmp_path / "tema.js").write_text("// tema claro u oscuro", encoding="utf-8")
    (tmp_path / "secreto.py").write_text("CLAVE = 1", encoding="utf-8")
    return tmp_path


def cliente(**config):
    app = create_app({"TESTING": True, "SECRET_KEY": "x", "SQLALCHEMY_DATABASE_URI": "sqlite://", **config})
    return app.test_client()


def test_la_raiz_sirve_la_app_sin_cache_y_con_cabeceras_de_seguridad(web):
    r = cliente(CARPETA_WEB=str(web)).get("/")
    assert r.status_code == 200 and b"Pachanga" in r.data
    assert r.headers["Cache-Control"] == "no-cache"
    assert "default-src 'self'" in r.headers["Content-Security-Policy"]
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["X-Content-Type-Options"] == "nosniff"


def test_los_assets_se_guardan_en_cache_mucho_tiempo(web):
    r = cliente(CARPETA_WEB=str(web)).get("/assets/index-abc123.js")
    assert r.status_code == 200 and "immutable" in r.headers["Cache-Control"]


def test_archivos_sueltos_permitidos_y_prohibidos(web):
    c = cliente(CARPETA_WEB=str(web))
    assert c.get("/favicon.svg").status_code == 200
    assert c.get("/manifest.webmanifest").status_code == 200
    assert c.get("/tema.js").status_code == 200
    assert c.get("/secreto.py").status_code == 404      # extensión no permitida
    assert c.get("/no-existe.png").status_code == 404
    assert c.get("/assets/../secreto.py").status_code == 404  # no se puede salir de la carpeta


def test_la_api_y_las_demas_rutas_siguen_funcionando(web):
    c = cliente(CARPETA_WEB=str(web))
    assert c.get("/health").get_json() == {"estado": "ok"}
    assert c.get("/api/avatares").status_code == 200
    assert c.get("/borrar-cuenta").status_code == 200
    assert c.get("/api/no-existe").status_code == 404


def test_sin_compilar_avisa_en_vez_de_romperse(tmp_path):
    r = cliente(CARPETA_WEB=str(tmp_path / "vacia")).get("/")
    assert r.status_code == 503 and "npm run build" in r.get_data(as_text=True)


def test_cors_desactivado_por_defecto(web):
    """En producción la web y la API comparten origen: ninguna otra web puede llamar a la API."""
    r = cliente(CARPETA_WEB=str(web), CORS_ORIGENES=[]).get("/health", headers={"Origin": "https://malvado.example"})
    assert "Access-Control-Allow-Origin" not in r.headers


def test_cors_de_desarrollo_permite_solo_localhost():
    c = cliente(CORS_ORIGENES=ORIGENES_DESARROLLO)
    r = c.get("/health", headers={"Origin": "http://127.0.0.1:5173"})
    assert r.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:5173"
    r = c.get("/health", headers={"Origin": "https://malvado.example"})
    assert "Access-Control-Allow-Origin" not in r.headers
