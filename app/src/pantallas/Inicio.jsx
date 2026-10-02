// Inicio: solo un resumen. Los equipos, la votación y el orden en portería están en la ficha
// de cada partido (se abre pulsando su tarjeta).
import { Link } from "react-router";
import Avatar from "../componentes/avatar/Avatar";
import { Cargando, MensajeError, Vacio } from "../componentes/Estados";
import { TarjetaJugado, TarjetaProximo } from "../componentes/partido/TarjetasPartido";
import { plural } from "../formato";
import { useCarga } from "../hooks/useCarga";
import { useSesion } from "../sesion";

const MEDALLAS = ["🥇", "🥈", "🥉"];
const ULTIMOS = 3;

function TopGoleadores() {
  const { datos, cargando, error, recargar } = useCarga("/api/clasificacion?orden=goles");
  if (cargando && !datos) return <Cargando />;
  if (error) return <MensajeError mensaje={error} reintentar={recargar} />;
  const top = datos.clasificacion.filter((f) => f.goles > 0).slice(0, 3);
  if (top.length === 0) return <Vacio>Todavía no hay goles confirmados.</Vacio>;
  return (
    <div className="tarjeta lista-top">
      {top.map((f, i) => (
        <Link key={f.id} to={`/jugador/${f.id}`} className="fila-top">
          <span className="medalla" aria-label={`Puesto ${i + 1}`}>{MEDALLAS[i]}</span>
          <Avatar avatar={f.avatar} tam={36} />
          <span className="nombre">{f.mote}</span>
          <span className="goles-top">{plural(f.goles, "gol", "goles")}</span>
        </Link>
      ))}
    </div>
  );
}

export default function Inicio() {
  const { usuario } = useSesion();
  const { datos, cargando, error, recargar } = useCarga("/api/partidos");

  let proximos = null;
  let jugados = null;
  if (cargando && !datos) proximos = <Cargando />;
  else if (error) proximos = <MensajeError mensaje={error} reintentar={recargar} />;
  else {
    // La API los da del más nuevo al más antiguo: los próximos se ordenan del más cercano al más lejano
    const abiertos = datos.partidos.filter((p) => p.estado === "abierto").reverse();
    const cerrados = datos.partidos.filter((p) => p.estado === "cerrado").slice(0, ULTIMOS);
    proximos = abiertos.length ? (
      <div className="lista">{abiertos.map((p) => <TarjetaProximo key={p.id} partido={p} destacada />)}</div>
    ) : (
      <Vacio>
        <p>No hay ningún partido programado.</p>
        {usuario.es_admin && <Link to="/partidos" className="btn btn-primario">+ Crear partido</Link>}
      </Vacio>
    );
    jugados = cerrados.length ? (
      <div className="lista">{cerrados.map((p) => <TarjetaJugado key={p.id} partido={p} />)}</div>
    ) : <Vacio>Todavía no se ha jugado ningún partido.</Vacio>;
  }

  return (
    <div className="pila">
      <h1 className="saludo">¡Hola, {usuario.mote}!</h1>
      <section>
        <h2 className="titulo-seccion">Próximo partido</h2>
        {proximos}
      </section>
      {jugados && (
        <section>
          <h2 className="titulo-seccion">Últimos partidos</h2>
          {jugados}
        </section>
      )}
      <section>
        <div className="fila-titulo">
          <h2 className="titulo-seccion">Máximos goleadores</h2>
          <Link to="/clasificacion" className="enlace-pequeno">Ver tabla ›</Link>
        </div>
        <TopGoleadores />
      </section>
    </div>
  );
}
