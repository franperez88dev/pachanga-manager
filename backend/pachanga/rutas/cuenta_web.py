"""Página web para borrar la cuenta sin la app (Google Play exige una URL así)."""
from flask import Blueprint, render_template_string, request

from ..errores import ErrorApi
from ..seguridad import verificar_credenciales
from ..servicios import borrar_usuario

bp = Blueprint("cuenta_web", __name__)

PLANTILLA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Borrar cuenta · Pachanga Manager</title>
<style>
  body{font-family:system-ui,sans-serif;max-width:480px;margin:0 auto;padding:24px 16px;background:#f1f4ee;color:#16211a;line-height:1.5}
  @media (prefers-color-scheme:dark){body{background:#0d1411;color:#e9efe8}input{background:#161f1a;color:#e9efe8}}
  h1{color:#0f7a4d;font-size:22px}
  label{display:block;font-weight:600;margin-top:12px}
  input[type=text],input[type=password]{width:100%;box-sizing:border-box;padding:10px;font-size:16px;border:1px solid #b9c5ad;border-radius:8px}
  button{margin-top:18px;width:100%;padding:12px;font-size:16px;font-weight:600;border:0;border-radius:8px;background:#c0392b;color:#fff}
  .aviso{padding:12px;border-radius:8px;margin:14px 0}
  .ok{background:#dff3e8}.error{background:#f7e4e1;color:#8b2418}
</style></head><body>
<h1>Borrar mi cuenta de Pachanga Manager</h1>
{% if hecho %}
  <p class="aviso ok">Tu cuenta y todos tus datos se han borrado.</p>
{% else %}
  <p>Se borrarán <b>de forma definitiva</b> tu cuenta y todos tus datos: mote, nombre real,
  dorsal, PIN, las valoraciones que diste y recibiste, tus goles, tus multas y tus huecos en los partidos.</p>
  <p>También puedes hacerlo desde la app, en <b>Perfil → Borrar mi cuenta</b>.</p>
  {% if error %}<p class="aviso error">{{ error }}</p>{% endif %}
  <form method="post">
    <label for="mote">Tu mote</label>
    <input type="text" id="mote" name="mote" required autocomplete="username">
    <label for="pin">Tu PIN</label>
    <input type="password" id="pin" name="pin" required inputmode="numeric" maxlength="4" autocomplete="current-password">
    <label><input type="checkbox" name="confirmar" value="si" required>
      Entiendo que el borrado no se puede deshacer</label>
    <button type="submit">Borrar mi cuenta para siempre</button>
  </form>
{% endif %}
</body></html>"""


@bp.route("/borrar-cuenta", methods=["GET", "POST"])
def borrar_cuenta():
    if request.method == "GET":
        return render_template_string(PLANTILLA)
    if request.form.get("confirmar") != "si":
        return render_template_string(PLANTILLA, error="Marca la casilla de confirmación"), 400
    try:
        usuario = verificar_credenciales(request.form.get("mote", ""), request.form.get("pin", ""))
        borrar_usuario(usuario)
    except ErrorApi as e:
        return render_template_string(PLANTILLA, error=e.mensaje), e.status
    return render_template_string(PLANTILLA, hecho=True)
