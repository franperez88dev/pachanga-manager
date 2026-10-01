// Los dos equipos sobre una pista de fútbol sala en horizontal.
// Coordenadas en decímetros: x de 0 a 400 (largo), y de 0 a 200 (ancho), con margen para las porterías.
import { Link } from "react-router";
import { EQUIPOS } from "../../config";
import { decimal } from "../../formato";
import Avatar from "../avatar/Avatar";

const VB = { x: -14, y: -10, w: 428, h: 220 };
const LINEA = { stroke: "#fff", strokeWidth: 1.6, fill: "none", opacity: 0.9 };

// Formación 1-2-2 del equipo de la izquierda (Nevados). El de la derecha es el espejo.
const FORMACION = {
  portero: [{ x: 30, y: 100 }],
  defensa: [{ x: 80, y: 38 }, { x: 80, y: 162 }], // al borde de su área (llega hasta x=60)
  delantero: [{ x: 150, y: 62 }, { x: 150, y: 138 }], // junto al círculo central, en su campo
};

function colocar(jugadores, derecha) {
  const usados = { portero: 0, defensa: 0, delantero: 0 };
  return jugadores.map((j) => {
    const sitio = FORMACION[j.posicion]?.[usados[j.posicion]++] ?? FORMACION.portero[0];
    const x = derecha ? 400 - sitio.x : sitio.x;
    const y = derecha ? 200 - sitio.y : sitio.y;
    return { ...j, left: ((x - VB.x) / VB.w) * 100, top: ((y - VB.y) / VB.h) * 100 };
  });
}

function LineasPista() {
  return (
    <svg viewBox={`${VB.x} ${VB.y} ${VB.w} ${VB.h}`} preserveAspectRatio="none" aria-hidden="true">
      {Array.from({ length: 8 }, (_, i) => (
        <rect key={i} x={i * 50} y="0" width="25" height="200" fill="#fff" opacity=".035" />
      ))}
      <rect x="0" y="0" width="400" height="200" {...LINEA} />
      <line x1="200" y1="0" x2="200" y2="200" {...LINEA} />
      <circle cx="200" cy="100" r="30" {...LINEA} />
      <circle cx="200" cy="100" r="1.8" fill="#fff" />
      <path d="M0,24.2 A60,60 0 0 1 60,84.2 L60,115.8 A60,60 0 0 1 0,175.8" {...LINEA} />
      <path d="M400,24.2 A60,60 0 0 0 340,84.2 L340,115.8 A60,60 0 0 0 400,175.8" {...LINEA} />
      {[60, 100, 300, 340].map((x) => <circle key={x} cx={x} cy="100" r="1.6" fill="#fff" />)}
      <path d="M2.5,0 A2.5,2.5 0 0 1 0,2.5 M0,197.5 A2.5,2.5 0 0 1 2.5,200 M397.5,0 A2.5,2.5 0 0 0 400,2.5 M400,197.5 A2.5,2.5 0 0 0 397.5,200" {...LINEA} />
      <rect x="-9" y="84.2" width="9" height="31.6" {...LINEA} />
      <rect x="400" y="84.2" width="9" height="31.6" {...LINEA} />
    </svg>
  );
}

function Ficha({ jugador, color }) {
  return (
    <Link to={`/jugador/${jugador.id}`} className={`ficha ${color}`}
      style={{ left: `${jugador.left}%`, top: `${jugador.top}%` }}>
      <span className="ficha-marco">
        <Avatar avatar={jugador.avatar} camiseta={EQUIPOS[color].camiseta} className="ficha-avatar" />
        <span className="ficha-dorsal">{jugador.dorsal}</span>
      </span>
      <span className="ficha-mote">{jugador.mote}</span>
    </Link>
  );
}

export default function Pista({ equipos }) {
  const { blanco, negro } = equipos;
  return (
    <div className="tarjeta pista-tarjeta">
      <div className="marcador">
        <div className="lado blanco">
          <img src={EQUIPOS.blanco.escudo} alt="" />
          <span className="nombre">{blanco.nombre}</span>
          <span className="fuerza">{decimal(blanco.fuerza)}</span>
        </div>
        <div className="vs">VS</div>
        <div className="lado negro">
          <img src={EQUIPOS.negro.escudo} alt="" />
          <span className="nombre">{negro.nombre}</span>
          <span className="fuerza">{decimal(negro.fuerza)}</span>
        </div>
      </div>
      <div className="pista">
        <LineasPista />
        {colocar(blanco.jugadores, false).map((j) => <Ficha key={j.id} jugador={j} color="blanco" />)}
        {colocar(negro.jugadores, true).map((j) => <Ficha key={j.id} jugador={j} color="negro" />)}
      </div>
    </div>
  );
}
