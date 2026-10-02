// /partidos/:id  ->  useParams() lee el ":id" de la dirección
import { useNavigate, useParams } from "react-router";
import { Cargando, MensajeError } from "../componentes/Estados";
import VistaPartido from "../componentes/partido/VistaPartido";
import { useCarga } from "../hooks/useCarga";

export default function PaginaPartido() {
  const { id } = useParams();
  const navegar = useNavigate();
  const { datos, cargando, error, recargar, poner } = useCarga(`/api/partidos/${id}`);

  // Vuelve a donde estabas (Inicio o Partidos). Si se abrió la ficha directamente, a la lista.
  const volver = () => (window.history.state?.idx > 0 ? navegar(-1) : navegar("/partidos"));

  return (
    <div className="pila">
      <button className="volver" onClick={volver}>‹ Volver</button>
      {cargando && !datos ? <Cargando /> : error ? <MensajeError mensaje={error} reintentar={recargar} /> : (
        <VistaPartido partido={datos.partido} alCambiar={(p) => poner({ partido: p })} />
      )}
    </div>
  );
}
