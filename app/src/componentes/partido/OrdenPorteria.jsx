// Orden en portería: un panel por equipo, con sus colores y el escudo de fondo
import { EQUIPOS } from "../../config";
import Avatar from "../avatar/Avatar";

function Panel({ equipo, color }) {
  const porId = Object.fromEntries(equipo.jugadores.map((j) => [j.id, j]));
  return (
    <div className={`porteria-panel ${color}`}>
      <img className="porteria-escudo" src={EQUIPOS[color].escudo} alt="" aria-hidden="true" />
      <h3>{equipo.nombre}</h3>
      <ol>
        {equipo.porteria.map((id, i) => (
          <li key={id}>
            <span className="turno">{i + 1}</span>
            <Avatar avatar={porId[id]?.avatar} tam={26} camiseta={EQUIPOS[color].camiseta} />
            <span className="nombre">{porId[id]?.mote}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

export default function OrdenPorteria({ equipos }) {
  return (
    <section>
      <h2 className="titulo-seccion">Orden en portería</h2>
      <div className="porteria">
        <Panel equipo={equipos.blanco} color="blanco" />
        <Panel equipo={equipos.negro} color="negro" />
      </div>
    </section>
  );
}
