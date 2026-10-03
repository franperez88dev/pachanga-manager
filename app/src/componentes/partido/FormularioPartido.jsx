/*
 * Formulario del admin para CREAR un partido o EDITAR uno abierto (día, lugar y precio).
 * Sirve para las dos cosas: si recibe `partido`, edita ese; si no, crea uno nuevo
 * (y `sugerido` es el partido anterior, para no volver a elegir el lugar y el precio).
 *
 * El precio siempre tiene la misma frase y solo se eligen tres huecos:
 *   Pagar a [quién] ([precio] € anticipado | [precio] € el día del partido)
 * Los desplegables ofrecen lo habitual y todo lo que ya se haya usado en otros partidos.
 */
import { useState } from "react";
import { api } from "../../api";
import { useAvisar } from "../../avisos";
import { leerPrecio, precio } from "../../formato";
import { useCarga } from "../../hooks/useCarga";
import { Cargando, MensajeError } from "../Estados";
import SelectorConOtro from "../SelectorConOtro";

const leerNombre = (texto) => texto.trim().replace(/\s+/g, " ") || null;
const textoPrecio = (centimos) => `${precio(centimos)} €`;

function Formulario({ partido, sugerido, opciones, alGuardar, alCancelar }) {
  const avisar = useAvisar();
  const inicial = partido ?? sugerido;
  const [fecha, setFecha] = useState(partido?.fecha ?? "");
  const [lugar, setLugar] = useState(inicial.lugar ?? "");
  // ?? = "si lo de la izquierda no existe, usa lo de la derecha": primero lo del partido,
  // y si no tiene, la primera opción del desplegable
  const [pagoA, setPagoA] = useState(inicial.pago_a ?? opciones.cobradores[0] ?? null);
  const [anticipado, setAnticipado] = useState(inicial.precio_anticipado ?? opciones.precios[0] ?? null);
  const [dia, setDia] = useState(inicial.precio_dia ?? opciones.precios.at(-1) ?? null);
  const [enviando, setEnviando] = useState(false);

  const precioCompleto = pagoA !== null && anticipado !== null && dia !== null;

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    try {
      const datos = { fecha, lugar, pago_a: pagoA, precio_anticipado: anticipado, precio_dia: dia };
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

      <div className="campo-precio">
        <div className="campo-etiqueta">Precio <small>(lo ven todos en la ficha del partido)</small></div>
        <div className="linea-precio">
          <span>Pagar a</span>
          <SelectorConOtro etiqueta="A quién se paga" opciones={opciones.cobradores} valor={pagoA} onChange={setPagoA}
            leer={leerNombre} placeholder="Nombre" maxLength={30} />
        </div>
        <div className="linea-precio">
          <SelectorConOtro etiqueta="Precio anticipado" opciones={opciones.precios} valor={anticipado}
            onChange={setAnticipado} texto={textoPrecio} leer={leerPrecio} placeholder="Ej: 2,2" inputMode="decimal" />
          <span>anticipado</span>
        </div>
        <div className="linea-precio">
          <SelectorConOtro etiqueta="Precio el día del partido" opciones={opciones.precios} valor={dia}
            onChange={setDia} texto={textoPrecio} leer={leerPrecio} placeholder="Ej: 2,5" inputMode="decimal" />
          <span>el día del partido</span>
        </div>
        <p className="nota">
          {precioCompleto
            ? <>Se verá así: <b>Pagar a {pagoA} ({precio(anticipado)} € anticipado | {precio(dia)} € el día del partido)</b></>
            : "Escribe el nombre y los precios en euros (por ejemplo 2,5)."}
        </p>
      </div>

      <div className="acciones">
        <button type="button" className="btn btn-suave" onClick={alCancelar}>Cancelar</button>
        <button className="btn btn-primario" disabled={enviando || !fecha || !lugar.trim() || !precioCompleto}>
          {partido ? "Guardar cambios" : "Crear partido"}
        </button>
      </div>
    </form>
  );
}

export default function FormularioPartido({ partido = null, sugerido = {}, alGuardar, alCancelar }) {
  // Primero se piden las opciones de los desplegables; el formulario se pinta cuando llegan
  const opciones = useCarga("/api/partidos/opciones-pago");
  if (opciones.cargando && !opciones.datos) return <div className="tarjeta relleno"><Cargando /></div>;
  if (opciones.error) {
    return <div className="tarjeta relleno"><MensajeError mensaje={opciones.error} reintentar={opciones.recargar} /></div>;
  }
  return <Formulario partido={partido} sugerido={sugerido} opciones={opciones.datos}
    alGuardar={alGuardar} alCancelar={alCancelar} />;
}
