/*
 * Cuadrícula de dos columnas con buscador para elegir a los 10 convocados.
 * FORMULARIO CONTROLADO: el texto del buscador vive en el estado de React (`busqueda`)
 * y el <input> siempre muestra ese valor; cada tecla actualiza el estado con onChange.
 */
import { useState } from "react";
import { api } from "../../api";
import { useAvisar } from "../../avisos";
import { useCarga } from "../../hooks/useCarga";
import Avatar from "../avatar/Avatar";
import { Cargando, MensajeError } from "../Estados";

const NECESARIOS = 10;
const normalizar = (t) => t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

export default function Convocatoria({ partido, alCambiar, alTerminar }) {
  const avisar = useAvisar();
  const jugadores = useCarga("/api/jugadores");
  const [seleccion, setSeleccion] = useState(() => new Set(partido.convocados.map((j) => j.id)));
  const [busqueda, setBusqueda] = useState("");
  const [guardando, setGuardando] = useState(false);
  const editando = partido.equipos_generados; // "Volver a elegir" con equipos ya hechos

  if (jugadores.cargando && !jugadores.datos) return <Cargando />;
  if (jugadores.error) return <MensajeError mensaje={jugadores.error} reintentar={jugadores.recargar} />;

  const n = seleccion.size;
  const filtro = normalizar(busqueda.trim());
  const visibles = jugadores.datos.jugadores.filter((j) =>
    !filtro || normalizar(`${j.mote} ${j.nombre_real ?? ""}`).includes(filtro));

  function alternar(id) {
    // El estado nunca se modifica "a mano": se crea un Set nuevo y React repinta
    const nueva = new Set(seleccion);
    if (nueva.has(id)) nueva.delete(id);
    else if (nueva.size < NECESARIOS) nueva.add(id);
    else { avisar(`Ya hay ${NECESARIOS}. Quita a alguien primero`); return; }
    setSeleccion(nueva);
  }

  async function guardar() {
    setGuardando(true);
    try {
      let datos = await api.put(`/api/partidos/${partido.id}/convocatoria`, { jugadores: [...seleccion] });
      if (!datos.partido.equipos_generados) {
        datos = await api.post(`/api/partidos/${partido.id}/equipos`, {});
        avisar("¡Equipos hechos!");
      } else {
        avisar("Mismos convocados: los equipos se mantienen");
      }
      alCambiar(datos.partido);
      alTerminar?.();
    } catch (e) {
      avisar(e.message);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <section>
      <div className="cabecera-convocatoria">
        <div>
          <div className="etiqueta-clara">Convocados</div>
          <div className="nota-clara">{n === NECESARIOS ? "✔ Ya tienes los 10" : n < NECESARIOS ? `Faltan ${NECESARIOS - n}` : ""}</div>
        </div>
        <div className="cuenta">{n}/{NECESARIOS}</div>
      </div>
      {editando && (
        <p className="nota">Si cambias a alguien, los equipos y la votación empiezan de cero. Con los mismos 10, no cambia nada.</p>
      )}
      <input className="campo" type="search" placeholder="Buscar por mote o nombre…" value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)} aria-label="Buscar jugador" />
      <div className="cuadricula-convocatoria">
        {visibles.map((j) => (
          <button key={j.id} type="button" className={`celda-convocado ${seleccion.has(j.id) ? "marcada" : ""}`}
            aria-pressed={seleccion.has(j.id)} onClick={() => alternar(j.id)}>
            <span className="casilla" aria-hidden="true">✓</span>
            <Avatar avatar={j.avatar} tam={30} />
            <span className="nombre">{j.mote}</span>
          </button>
        ))}
      </div>
      {visibles.length === 0 && <p className="nota centrado">Nadie coincide con la búsqueda.</p>}
      <div className="acciones">
        {editando && <button className="btn btn-suave" onClick={alTerminar}>Cancelar</button>}
        <button className="btn btn-primario btn-ancho" disabled={n !== NECESARIOS || guardando} onClick={guardar}>
          {editando ? "Guardar convocatoria" : "⚙️ Crear equipos (Blanco vs Negro)"}
        </button>
      </div>
      {n !== NECESARIOS && <p className="nota centrado">Necesitas exactamente {NECESARIOS} convocados.</p>}
    </section>
  );
}
