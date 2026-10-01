// El admin cierra el partido indicando cómo ha terminado
import { useState } from "react";
import { api } from "../../api";
import { useAvisar } from "../../avisos";
import { EQUIPOS } from "../../config";
import Contador from "../Contador";

export default function CerrarPartido({ partido, alCambiar, alCancelar }) {
  const avisar = useAvisar();
  const [goles, setGoles] = useState({ blanco: 0, negro: 0 });
  const [enviando, setEnviando] = useState(false);

  async function confirmar() {
    setEnviando(true);
    try {
      const datos = await api.post(`/api/partidos/${partido.id}/cerrar`,
        { goles_blanco: goles.blanco, goles_negro: goles.negro });
      avisar("Partido cerrado");
      alCambiar(datos.partido);
    } catch (e) {
      avisar(e.message);
      setEnviando(false);
    }
  }

  return (
    <div className="tarjeta relleno">
      <h3 className="titulo-tarjeta">¿Cómo ha terminado?</h3>
      <div className="resultado-editor">
        {["blanco", "negro"].map((color) => (
          <div key={color} className="resultado-equipo">
            <img src={EQUIPOS[color].escudo} alt="" />
            <span className="nombre">{EQUIPOS[color].nombre}</span>
            <Contador valor={goles[color]} max={99} etiqueta={`goles de ${EQUIPOS[color].nombre}`}
              onChange={(v) => setGoles({ ...goles, [color]: v })} />
          </div>
        ))}
      </div>
      <div className="acciones">
        <button className="btn btn-suave" onClick={alCancelar}>Cancelar</button>
        <button className="btn btn-primario" disabled={enviando} onClick={confirmar}>
          Cerrar partido {goles.blanco}–{goles.negro}
        </button>
      </div>
    </div>
  );
}
