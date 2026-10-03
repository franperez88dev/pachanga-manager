// Lista de partidos y, para el admin, el formulario para crear uno nuevo
import { useState } from "react";
import { useNavigate } from "react-router";
import { useAvisar } from "../avisos";
import { Cargando, MensajeError, Vacio } from "../componentes/Estados";
import FormularioPartido from "../componentes/partido/FormularioPartido";
import { TarjetaJugado, TarjetaProximo } from "../componentes/partido/TarjetasPartido";
import { useCarga } from "../hooks/useCarga";
import { useSesion } from "../sesion";

export default function Partidos() {
  const { usuario } = useSesion();
  const avisar = useAvisar();
  const navegar = useNavigate();
  const { datos, cargando, error, recargar } = useCarga("/api/partidos");
  const [creando, setCreando] = useState(false);
  // Para no reescribirlos cada semana: el lugar y el precio del partido más reciente
  const anterior = datos?.partidos[0];

  function alCrear(partido) {
    avisar("Partido creado. Ya se pueden apuntar");
    navegar(`/partidos/${partido.id}`);
  }

  return (
    <div className="pila">
      <div className="fila-titulo">
        <h1 className="titulo-pagina">Partidos</h1>
        {usuario.es_admin && !creando && <button className="btn btn-primario" onClick={() => setCreando(true)}>+ Nuevo</button>}
      </div>
      {creando && (
        <FormularioPartido sugerido={anterior ?? {}}
          alGuardar={alCrear} alCancelar={() => setCreando(false)} />
      )}
      {cargando && !datos ? <Cargando /> : error ? <MensajeError mensaje={error} reintentar={recargar} /> :
        datos.partidos.length === 0 ? <Vacio>Todavía no hay partidos.</Vacio> : (
          <div className="lista">
            {datos.partidos.map((p) => (p.estado === "abierto"
              ? <TarjetaProximo key={p.id} partido={p} />
              : <TarjetaJugado key={p.id} partido={p} />))}
          </div>
        )}
    </div>
  );
}
