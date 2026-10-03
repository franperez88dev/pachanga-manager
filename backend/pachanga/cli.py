"""Comandos de terminal: `flask create-admin` y, solo para probar en local, `flask datos-demo`
y `flask demo-votar`."""
import random

import click

from .errores import ErrorApi
from .extensions import db
from .models import ESTADO_APROBADO, ROL_ADMIN, Match, Rating, User, VotoRebarajar
from .seguridad import hash_pin
from .servicios import crear_usuario

MOTES_DEMO = ["Feragi", "Chuti", "El Tanke", "Rulo", "Kike", "Nino",
              "Josemi", "Payo", "Sergi", "Toni", "Manu", "Guaje"]
PIN_DEMO = "1111"


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

    def solo_en_local():
        # En PythonAnywhere este interruptor NO se pone: así es imposible crear allí por error
        # jugadores de prueba con un PIN que conoce todo el mundo.
        if not app.config["PERMITIR_DATOS_DEMO"]:
            raise click.ClickException(
                "Este comando es solo para pruebas en tu PC. Para activarlo, pon PERMITIR_DATOS_DEMO=1 "
                "en backend/.env (NUNCA en el servidor de verdad).")

    @app.cli.command("datos-demo")
    def datos_demo():
        """SOLO PRUEBAS: 12 jugadores aprobados (PIN 1111) y valoraciones al azar."""
        solo_en_local()
        creados = []
        for mote in MOTES_DEMO:
            if User.query.filter_by(mote=mote).first():
                continue
            u, _ = crear_usuario(mote, estado=ESTADO_APROBADO)
            u.pin_hash = hash_pin(PIN_DEMO)
            creados.append(u)
        db.session.flush()

        # Cada jugador de prueba valora a todos los demás (menos a sí mismo) con 1-5 estrellas
        aprobados = User.query.filter_by(estado=ESTADO_APROBADO).all()
        azar = random.Random()
        for u in creados:
            for otro in aprobados:
                if otro.id != u.id:
                    db.session.add(Rating(rater_id=u.id, rated_id=otro.id, stars=azar.randint(1, 5)))
        db.session.commit()

        if not creados:
            click.echo("Los jugadores de prueba ya existían; no se ha creado nada.")
            return
        click.secho(f"\n  {len(creados)} jugadores de prueba creados. Todos entran con el PIN {PIN_DEMO}:",
                    fg="green", bold=True)
        for u in creados:
            click.echo(f"    {u.dorsal:>2}  {u.mote}")

    @app.cli.command("demo-votar")
    @click.argument("partido_id", type=int)
    @click.option("--si", default=5, show_default=True, help="Cuántos votan que sí")
    @click.option("--no", "no_", default=0, show_default=True, help="Cuántos votan que no")
    def demo_votar(partido_id, si, no_):
        """SOLO PRUEBAS: hace votar a los jugadores de prueba convocados en un partido."""
        solo_en_local()
        partido = db.session.get(Match, partido_id)
        if partido is None or not partido.equipos_generados:
            raise click.ClickException("Ese partido no existe o todavía no tiene equipos.")
        ya = {v.user_id for v in VotoRebarajar.query.filter_by(match_id=partido.id, ronda=partido.num_repartos)}
        libres = [mp.usuario for mp in partido.jugadores
                  if mp.usuario.mote in MOTES_DEMO and mp.user_id not in ya]
        if si + no_ > len(libres):
            raise click.ClickException(f"Solo quedan {len(libres)} jugadores de prueba sin votar.")
        for i, u in enumerate(libres[:si + no_]):
            db.session.add(VotoRebarajar(match_id=partido.id, user_id=u.id, ronda=partido.num_repartos,
                                         cambiar=i < si))
        db.session.commit()
        click.echo(f"Votos añadidos: {si} sí y {no_} no.")
