// /partidos/:id  ->  useParams() lee el ":id" de la dirección
import { Link, useParams } from "react-router";
import { Cargando, MensajeError } from "../componentes/Estados";
import VistaPartido from "../componentes/partido/VistaPartido";
import { useCarga } from "../hooks/useCarga";

export default function PaginaPartido() {
  const { id } = useParams();
  const { datos, cargando, error, recargar, poner } = useCarga(`/api/partidos/${id}`);

  return (
    <div className="pila">
      <Link to="/partidos" className="volver">‹ Partidos</Link>
      {cargando && !datos ? <Cargando /> : error ? <MensajeError mensaje={error} reintentar={recargar} /> : (
        <VistaPartido partido={datos.partido} alCambiar={(p) => poner({ partido: p })} />
      )}
    </div>
  );
}
