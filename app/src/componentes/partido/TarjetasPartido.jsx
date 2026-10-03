// Tarjetas resumidas de partidos (para Inicio y la lista de Partidos). Al pulsarlas se abre la ficha.
import { Link } from "react-router";
import { EQUIPOS } from "../../config";
import { fechaPartido } from "../../formato";

// Mi situación en el partido, en una etiqueta de color
function MiEstado({ partido }) {
  if (partido.convocado) return <span className="etiqueta-estado confirmado">Tienes hueco ✔</span>;
  if (partido.soy_reserva) return <span className="etiqueta-estado pendiente">Reserva · puesto {partido.mi_puesto}</span>;
  return <span className="etiqueta-estado gris">Sin apuntar</span>;
}

// `destacada`: fondo verde suave (se usa en Inicio para distinguirlos de los ya jugados)
export function TarjetaProximo({ partido, destacada = false }) {
  const juegan = Math.min(partido.num_apuntados, partido.plazas);
  let estado;
  if (partido.equipos_generados) {
    estado = partido.convocado ? <>Juegas con <b>{EQUIPOS[partido.mi_equipo].nombre}</b></> : "Equipos hechos";
  } else if (juegan < partido.plazas) {
    estado = `${juegan}/${partido.plazas} apuntados`;
  } else {
    estado = partido.num_reservas ? `Completo · ${partido.num_reservas} de reserva` : "Completo";
  }

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
        <MiEstado partido={partido} />
        <span className="nota">{estado}</span>
      </div>
      {!partido.apuntado && !partido.lista_cerrada && (
        <div className="aviso-votar">✋ Entra para {juegan < partido.plazas ? "reservar tu hueco" : "apuntarte de reserva"}</div>
      )}
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
