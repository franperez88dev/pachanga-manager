/*
 * Formulario del admin para CREAR un partido o EDITAR uno abierto (día, lugar y precio).
 * Sirve para las dos cosas: si recibe `partido`, edita ese; si no, crea uno nuevo
 * (y `sugerido` trae el lugar y el precio del partido anterior, para no reescribirlos).
 */
import { useState } from "react";
import { api } from "../../api";
import { useAvisar } from "../../avisos";

const MAX_PRECIO = 200;

export default function FormularioPartido({ partido = null, sugerido = {}, alGuardar, alCancelar }) {
  const avisar = useAvisar();
  const [fecha, setFecha] = useState(partido?.fecha ?? "");
  const [lugar, setLugar] = useState(partido?.lugar ?? sugerido.lugar ?? "");
  const [infoPago, setInfoPago] = useState(partido?.info_pago ?? sugerido.info_pago ?? "");
  const [enviando, setEnviando] = useState(false);

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    try {
      const datos = { fecha, lugar, info_pago: infoPago };
      const respuesta = partido
        ? await api.patch(`/api/partidos/${partido.id}`, datos)
        : await api.post("/api/partidos", datos);
      alGuardar(respuesta.partido);
    } catch (err) {
      avisar(err.message);
      setEnviando(false);
    }
  }

  return (
    <form className="tarjeta relleno formulario" onSubmit={enviar}>
      <h3 className="titulo-tarjeta">{partido ? "Editar partido" : "Nuevo partido"}</h3>
      <label className="campo-etiqueta">
        Día y hora
        <input className="campo" type="datetime-local" value={fecha} onChange={(e) => setFecha(e.target.value)} required />
      </label>
      <label className="campo-etiqueta">
        Lugar
        <input className="campo" value={lugar} onChange={(e) => setLugar(e.target.value)} maxLength={80}
          placeholder="Ej: Polideportivo municipal" required />
      </label>
      <label className="campo-etiqueta">
        Precio y a quién se paga <small>(opcional · lo ven todos)</small>
        <textarea className="campo" rows={2} value={infoPago} maxLength={MAX_PRECIO}
          onChange={(e) => setInfoPago(e.target.value)}
          placeholder="Ej: Pagar a Feragi (2,2 € anticipado | 2,5 € el día del partido)" />
      </label>
      <div className="acciones">
        <button type="button" className="btn btn-suave" onClick={alCancelar}>Cancelar</button>
        <button className="btn btn-primario" disabled={enviando || !fecha || !lugar.trim()}>
          {partido ? "Guardar cambios" : "Crear partido"}
        </button>
      </div>
    </form>
  );
}
