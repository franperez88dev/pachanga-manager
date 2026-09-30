"""Comandos de terminal: `flask create-admin`."""
import click

from .errores import ErrorApi
from .extensions import db
from .models import ESTADO_APROBADO, ROL_ADMIN, User
from .servicios import crear_usuario


def registrar_comandos(app):
    @app.cli.command("create-admin")
    @click.option("--mote", prompt="Mote del admin", help="Mote con el que entrarás en la app")
    @click.option("--nombre-real", prompt="Nombre real (opcional, Enter para dejarlo vacío)",
                  default="", show_default=False)
    def create_admin(mote, nombre_real):
        """Crea el primer admin (dorsal 01 si la base de datos está vacía)."""
        if User.query.filter_by(rol=ROL_ADMIN).first():
            raise click.ClickException("Ya hay un admin. Los siguientes se nombran desde el panel de admin.")
        try:
            u, pin = crear_usuario(mote, nombre_real, rol=ROL_ADMIN, estado=ESTADO_APROBADO)
        except ErrorApi as e:
            raise click.ClickException(e.mensaje)
        db.session.commit()
        click.echo("")
        click.secho(f"  Admin '{u.mote}' creado con el dorsal {u.dorsal:02d}.", fg="green", bold=True)
        click.secho(f"  Tu PIN es: {pin}", fg="green", bold=True)
        click.echo("  Entras con tu mote + PIN. Apúntalo: no se puede volver a consultar.")
        if u.dorsal != 1:
            click.secho("  Aviso: ya había usuarios registrados, por eso no te ha tocado el 01.", fg="yellow")
