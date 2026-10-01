// Para un convocado, con el partido ya cerrado: apuntar sus goles (y gpp) y ver cómo va el reporte
import { useState } from "react";
import { api } from "../../api";
import { useAvisar } from "../../avisos";
import { useCarga } from "../../hooks/useCarga";
import { plural } from "../../formato";
import BotonConfirmar from "../BotonConfirmar";
import Contador from "../Contador";
import { Cargando, MensajeError } from "../Estados";

const ESTADOS = { pendiente: "Pendiente de que lo confirme el admin", confirmado: "Confirmado ✔" };

export default function MisGoles({ partido }) {
  const avisar = useAvisar();
  const mios = useCarga("/api/reportes/mios");
  const [goles, setGoles] = useState(0);
  const [gpp, setGpp] = useState(0);
  const [enviando, setEnviando] = useState(false);

  if (mios.cargando && !mios.datos) return <Cargando />;
  if (mios.error) return <MensajeError mensaje={mios.error} reintentar={mios.recargar} />;

  const activo = mios.datos.reportes.find((r) => r.partido.id === partido.id && ESTADOS[r.estado]);

  async function enviar() {
    setEnviando(true);
    try {
      await api.post(`/api/partidos/${partido.id}/reportes`, { goles, gpp });
      avisar("Enviado. Falta que lo confirme el admin");
      mios.recargar();
    } catch (e) {
      avisar(e.message);
    } finally {
      setEnviando(false);
    }
  }

  async function anular() {
    try {
      await api.post(`/api/reportes/${activo.id}/anular`);
      avisar("Anulado");
      mios.recargar();
    } catch (e) {
      avisar(e.message);
    }
  }

  return (
    <section>
      <h2 className="titulo-seccion">Mis goles en este partido</h2>
      {activo ? (
        <div className="tarjeta fila-reporte">
          <div>
            <div className="fuerte">{plural(activo.goles, "gol", "goles")}{activo.gpp > 0 && ` · ${activo.gpp} gpp`}</div>
            <div className={`etiqueta-estado ${activo.estado}`}>{ESTADOS[activo.estado]}</div>
          </div>
          {activo.estado === "pendiente" && (
            <BotonConfirmar pregunta="¿Seguro? Anular" onConfirmar={anular}>Anular</BotonConfirmar>
          )}
        </div>
      ) : (
        <div className="tarjeta relleno">
          <div className="linea-contador"><span>Goles</span><Contador valor={goles} onChange={setGoles} etiqueta="goles" /></div>
          <div className="linea-contador">
            <span>Goles en propia puerta <small>(cuentan para el rival)</small></span>
            <Contador valor={gpp} onChange={setGpp} etiqueta="goles en propia puerta" />
          </div>
          <button className="btn btn-primario btn-ancho" disabled={enviando || goles + gpp === 0} onClick={enviar}>
            Enviar al admin
          </button>
        </div>
      )}
    </section>
  );
}
