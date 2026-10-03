/*
 * La lista de apuntados, numerada como en el grupo de WhatsApp: del 1 al 10 juegan y,
 * del 11 en adelante, son reservas. Con `gestionar` (el admin) cada fila tiene una ✕ para
 * quitar a ese jugador (con o sin multa) y debajo hay un desplegable para apuntar a otro.
 */
import { useState } from "react";
import { Link } from "react-router";
import { api } from "../../api";
import { useAvisar } from "../../avisos";
import { useCarga } from "../../hooks/useCarga";
import { useSesion } from "../../sesion";
import Avatar from "../avatar/Avatar";

function Fila({ jugador, soyYo, gestionar, abierta, alAbrir, alQuitar, avisoEquipos }) {
  return (
    <li className={soyYo ? "yo" : ""}>
      <div className="fila-apuntado">
        <span className="puesto">{jugador.puesto})</span>
        <Avatar avatar={jugador.avatar} tam={30} />
        <Link to={`/jugador/${jugador.id}`} className="nombre">{jugador.mote}</Link>
        {gestionar && (
          <button type="button" className="boton-quitar" aria-label={`Quitar a ${jugador.mote}`}
            aria-expanded={abierta} onClick={alAbrir}>✕</button>
        )}
      </div>
      {abierta && (
        <div className="panel-quitar">
          <p className="nota">
            ¿Quitar a <b>{jugador.mote}</b> del partido?
            {avisoEquipos && " Los equipos se deshacen y tendrás que crearlos otra vez."}
          </p>
          <div className="acciones">
            <button type="button" className="btn btn-suave btn-pequeno" onClick={alAbrir}>Cancelar</button>
            <button type="button" className="btn btn-suave btn-pequeno" onClick={() => alQuitar(false)}>Quitar</button>
            <button type="button" className="btn btn-peligro btn-pequeno" onClick={() => alQuitar(true)}>Quitar con multa</button>
          </div>
        </div>
      )}
    </li>
  );
}

function ApuntarJugador({ partido, alCambiar }) {
  const avisar = useAvisar();
  const jugadores = useCarga("/api/jugadores");
  const [elegido, setElegido] = useState("");
  const [enviando, setEnviando] = useState(false);

  const yaEstan = new Set(partido.apuntados.map((j) => j.id));
  const disponibles = (jugadores.datos?.jugadores ?? []).filter((j) => !yaEstan.has(j.id));

  async function apuntar() {
    setEnviando(true);
    try {
      const datos = await api.post(`/api/partidos/${partido.id}/jugadores`, { user_id: Number(elegido) });
      alCambiar(datos.partido);
      setElegido("");
    } catch (e) {
      avisar(e.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="pie-lista">
      <span className="etiqueta-admin">Admin</span>
      <div className="fila-apuntar">
        {/* <select> controlado: su valor vive en el estado `elegido` (el id del jugador, como texto) */}
        <select className="campo" value={elegido} onChange={(e) => setElegido(e.target.value)}
          aria-label="Jugador que quieres apuntar" disabled={disponibles.length === 0}>
          <option value="">{disponibles.length ? "Apuntar a un jugador…" : "Ya están todos apuntados"}</option>
          {disponibles.map((j) => <option key={j.id} value={j.id}>{j.mote}</option>)}
        </select>
        <button type="button" className="btn btn-primario" disabled={!elegido || enviando} onClick={apuntar}>Apuntar</button>
      </div>
      {partido.equipos_generados && (
        <p className="nota">Con los equipos hechos, a quien apuntes entra de reserva.</p>
      )}
    </div>
  );
}

export default function ListaApuntados({ partido, alCambiar, gestionar = false }) {
  const { usuario } = useSesion();
  const avisar = useAvisar();
  const [quitando, setQuitando] = useState(null); // id del jugador con el panel "¿Quitar?" abierto

  const juegan = partido.apuntados.filter((j) => !j.reserva);
  const reservas = partido.apuntados.filter((j) => j.reserva);
  // Filas vacías hasta llegar a 10 (solo mientras la gente aún se puede apuntar)
  const libres = partido.equipos_generados ? 0 : Math.max(partido.plazas - juegan.length, 0);

  async function quitar(jugador, conMulta) {
    try {
      const datos = await api.borrar(`/api/partidos/${partido.id}/jugadores/${jugador.id}`, { multa: conMulta });
      alCambiar(datos.partido);
      avisar(conMulta ? `${jugador.mote} quitado, con multa` : `${jugador.mote} quitado`);
    } catch (e) {
      avisar(e.message);
    } finally {
      setQuitando(null);
    }
  }

  const fila = (j) => (
    <Fila key={j.id} jugador={j} soyYo={j.id === usuario.id} gestionar={gestionar}
      abierta={quitando === j.id} alAbrir={() => setQuitando(quitando === j.id ? null : j.id)}
      alQuitar={(conMulta) => quitar(j, conMulta)}
      avisoEquipos={partido.equipos_generados && !j.reserva} />
  );

  let resumen = "✔ Completo";
  if (libres > 0) resumen = libres === 1 ? "Falta 1" : `Faltan ${libres}`;
  else if (reservas.length) resumen = `✔ Completo · ${reservas.length} de reserva`;

  return (
    <section className="tarjeta tarjeta-lista">
      <div className="cabecera-lista">
        <div>
          <div className="etiqueta-clara">Apuntados</div>
          <div className="nota-clara">{resumen}</div>
        </div>
        <div className="cuenta">{juegan.length}/{partido.plazas}</div>
      </div>
      <ol className="lista-apuntados">
        {juegan.map(fila)}
        {Array.from({ length: libres }, (_, i) => (
          <li key={`libre-${i}`} className="libre">
            <div className="fila-apuntado">
              <span className="puesto">{juegan.length + i + 1})</span>
              <span className="hueco-vacio" aria-hidden="true" />
              <span className="nombre">Hueco libre</span>
            </div>
          </li>
        ))}
      </ol>
      {reservas.length > 0 && (
        <>
          <div className="titulo-reservas">Reservas</div>
          <ol className="lista-apuntados">{reservas.map(fila)}</ol>
        </>
      )}
      {gestionar && <ApuntarJugador partido={partido} alCambiar={alCambiar} />}
    </section>
  );
}
