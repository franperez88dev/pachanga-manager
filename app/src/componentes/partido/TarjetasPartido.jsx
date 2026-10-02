// Tarjetas resumidas de partidos (para Inicio y la lista de Partidos). Al pulsarlas se abre la ficha.
import { Link } from "react-router";
import { EQUIPOS } from "../../config";
import { fechaPartido } from "../../formato";

// `destacada`: fondo verde suave (se usa en Inicio para distinguirlos de los ya jugados)
export function TarjetaProximo({ partido, destacada = false }) {
  let estado;
  if (!partido.equipos_generados) estado = partido.num_convocados === 10 ? "Equipos por hacer" : "Convocatoria pendiente";
  else if (partido.convocado) estado = <>Juegas con <b>{EQUIPOS[partido.mi_equipo].nombre}</b></>;
  else estado = "Equipos hechos";

  return (
    <Link to={`/partidos/${partido.id}`} className={`tarjeta tarjeta-partido ${destacada ? "destacada" : ""}`}>
      <div className="tarjeta-partido-fila">
        <div className="tarjeta-partido-texto">
          <div className="fecha-partido">{fechaPartido(partido.fecha)}</div>
          <div className="lugar-partido">📍 {partido.lugar}</div>
        </div>
        <span className="flecha" aria-hidden="true">›</span>
      </div>
      <div className="tarjeta-partido-pie">
        <span className={`etiqueta-estado ${partido.convocado ? "confirmado" : ""}`}>
          {partido.convocado ? "Convocado ✔" : "No convocado"}
        </span>
        <span className="nota">{estado}</span>
      </div>
      {partido.debo_votar && (
        <div className="aviso-votar">🗳️ Tienes pendiente votar si quieres otro reparto de equipos</div>
      )}
    </Link>
  );
}

export function TarjetaJugado({ partido }) {
  const { blanco, negro } = partido.resultado;
  return (
    <Link to={`/partidos/${partido.id}`} className="tarjeta tarjeta-jugado">
      <span className="tarjeta-jugado-fecha">{fechaPartido(partido.fecha, true)}</span>
      <span className="tarjeta-jugado-marcador">
        <img src={EQUIPOS.blanco.escudo} alt={EQUIPOS.blanco.nombre} />
        <b>{blanco}–{negro}</b>
        <img src={EQUIPOS.negro.escudo} alt={EQUIPOS.negro.nombre} />
      </span>
      <span className="flecha" aria-hidden="true">›</span>
    </Link>
  );
}
