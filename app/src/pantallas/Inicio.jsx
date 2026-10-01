import { Link } from "react-router";
import { Cargando, MensajeError, Vacio } from "../componentes/Estados";
import VistaPartido, { Resultado } from "../componentes/partido/VistaPartido";
import { fechaPartido } from "../formato";
import { useCarga } from "../hooks/useCarga";
import { useSesion } from "../sesion";

function UltimoPartido() {
  const lista = useCarga("/api/partidos");
  const ultimo = lista.datos?.partidos.find((p) => p.estado === "cerrado");
  if (!ultimo) return null;
  return (
    <section>
      <h2 className="titulo-seccion">Último partido · {fechaPartido(ultimo.fecha, true)}</h2>
      <Link to={`/partidos/${ultimo.id}`} className="enlace-tarjeta">
        <Resultado partido={ultimo} />
      </Link>
    </section>
  );
}

export default function Inicio() {
  const { usuario } = useSesion();
  const proximo = useCarga("/api/partidos/proximo");

  let contenido;
  if (proximo.cargando && !proximo.datos) contenido = <Cargando />;
  else if (proximo.error) contenido = <MensajeError mensaje={proximo.error} reintentar={proximo.recargar} />;
  else if (!proximo.datos.partido) {
    contenido = (
      <Vacio>
        <p>No hay ningún partido programado.</p>
        {usuario.es_admin && <Link to="/partidos" className="btn btn-primario">+ Crear partido</Link>}
      </Vacio>
    );
  } else {
    // Si el admin lo cierra desde aquí, se sigue viendo (para apuntar los goles) hasta cambiar de pantalla
    contenido = <VistaPartido partido={proximo.datos.partido} alCambiar={(p) => proximo.poner({ partido: p })} />;
  }

  return (
    <div className="pila">
      <h1 className="saludo">¡Hola, {usuario.mote}!</h1>
      <section>
        <h2 className="titulo-seccion">Próximo partido</h2>
        {contenido}
      </section>
      <UltimoPartido />
    </div>
  );
}
