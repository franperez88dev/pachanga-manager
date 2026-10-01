// "¿Deseas una nueva selección de equipo?" para los convocados. Un voto por reparto.
import { useState } from "react";
import { api } from "../../api";
import { useAvisar } from "../../avisos";

export function BarraVotos({ votacion }) {
  const { votos_si: si, votos_no: no, votos_necesarios: necesarios } = votacion;
  return (
    <>
      <div className="barra-votos">
        <span style={{ width: `${(si / 10) * 100}%` }} />
        <i style={{ left: `${(necesarios / 10) * 100}%` }} />
      </div>
      <div className="recuento">
        <span>Sí: {si} · No: {no} · Sin votar: {10 - si - no}</span>
        <span>Hacen falta {necesarios}</span>
      </div>
    </>
  );
}

export default function Votacion({ partido, alCambiar }) {
  const avisar = useAvisar();
  const [enviando, setEnviando] = useState(false);
  const v = partido.votacion;

  async function votar(cambiar) {
    setEnviando(true);
    try {
      const datos = await api.post(`/api/partidos/${partido.id}/voto`, { cambiar });
      alCambiar(datos.partido);
      avisar("Voto registrado");
    } catch (e) {
      avisar(e.message);
    } finally {
      setEnviando(false);
    }
  }

  if (!v.abierta) {
    return (
      <div className="tarjeta votacion">
        <p className="nota">Equipos definitivos: ya se han hecho los {v.repartos_maximos} repartos.</p>
      </div>
    );
  }
  const yaVotado = v.mi_voto !== null;
  return (
    <div className="tarjeta votacion">
      <h3>¿Deseas una nueva selección de equipo?</h3>
      <p className="nota">
        {yaVotado
          ? `Has votado "${v.mi_voto ? "Sí" : "No"}". Podrás volver a votar si el admin hace un nuevo reparto.`
          : `Reparto ${v.repartos_hechos} de ${v.repartos_maximos}. Solo puedes votar una vez.`}
      </p>
      <div className="botones-voto">
        <button className="btn btn-primario" aria-pressed={v.mi_voto === true} disabled={yaVotado || enviando}
          onClick={() => votar(true)}>Sí</button>
        <button className="btn btn-suave" aria-pressed={v.mi_voto === false} disabled={yaVotado || enviando}
          onClick={() => votar(false)}>No</button>
      </div>
      <BarraVotos votacion={v} />
    </div>
  );
}
