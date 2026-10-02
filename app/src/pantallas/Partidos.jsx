// Lista de partidos y, para el admin, el formulario para crear uno nuevo
import { useState } from "react";
import { useNavigate } from "react-router";
import { api } from "../api";
import { useAvisar } from "../avisos";
import { Cargando, MensajeError, Vacio } from "../componentes/Estados";
import { TarjetaJugado, TarjetaProximo } from "../componentes/partido/TarjetasPartido";
import { useCarga } from "../hooks/useCarga";
import { useSesion } from "../sesion";

function NuevoPartido({ alCancelar }) {
  const avisar = useAvisar();
  const navegar = useNavigate();
  const [fecha, setFecha] = useState("");
  const [lugar, setLugar] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function crear(e) {
    e.preventDefault();
    setEnviando(true);
    try {
      const datos = await api.post("/api/partidos", { fecha, lugar });
      avisar("Partido creado. Ahora elige a los 10");
      navegar(`/partidos/${datos.partido.id}`);
    } catch (err) {
      avisar(err.message);
      setEnviando(false);
    }
  }

  return (
    <form className="tarjeta relleno formulario" onSubmit={crear}>
      <h3 className="titulo-tarjeta">Nuevo partido</h3>
      <label className="campo-etiqueta">
        Día y hora
        <input className="campo" type="datetime-local" value={fecha} onChange={(e) => setFecha(e.target.value)} required />
      </label>
      <label className="campo-etiqueta">
        Lugar
        <input className="campo" value={lugar} onChange={(e) => setLugar(e.target.value)} maxLength={80}
          placeholder="Ej: Polideportivo municipal" required />
      </label>
      <div className="acciones">
        <button type="button" className="btn btn-suave" onClick={alCancelar}>Cancelar</button>
        <button className="btn btn-primario" disabled={enviando || !fecha || !lugar.trim()}>Crear partido</button>
      </div>
    </form>
  );
}

export default function Partidos() {
  const { usuario } = useSesion();
  const { datos, cargando, error, recargar } = useCarga("/api/partidos");
  const [creando, setCreando] = useState(false);

  return (
    <div className="pila">
      <div className="fila-titulo">
        <h1 className="titulo-pagina">Partidos</h1>
        {usuario.es_admin && !creando && <button className="btn btn-primario" onClick={() => setCreando(true)}>+ Nuevo</button>}
      </div>
      {creando && <NuevoPartido alCancelar={() => setCreando(false)} />}
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
