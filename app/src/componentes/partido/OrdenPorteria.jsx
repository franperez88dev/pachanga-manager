import Avatar from "../avatar/Avatar";

function Columna({ equipo, color }) {
  const porId = Object.fromEntries(equipo.jugadores.map((j) => [j.id, j]));
  return (
    <div className={`porteria-columna ${color}`}>
      <h3>{equipo.nombre}</h3>
      <ol>
        {equipo.porteria.map((id, i) => (
          <li key={id}>
            <span className="turno">{i + 1}</span>
            <Avatar avatar={porId[id]?.avatar} tam={26} />
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
      <div className="tarjeta porteria">
        <Columna equipo={equipos.blanco} color="blanco" />
        <Columna equipo={equipos.negro} color="negro" />
      </div>
    </section>
  );
}
