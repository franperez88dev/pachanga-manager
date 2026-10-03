/*
 * Desplegable con una última opción "Añadir otro…": al elegirla aparece un campo para
 * escribir un valor nuevo. Se usa en el precio del partido (a quién se paga y cuánto).
 *
 *   opciones  lista de valores que se ofrecen (textos o números)
 *   valor     el valor elegido ahora (null = ninguno válido todavía)
 *   onChange  recibe el valor nuevo, o null si lo escrito en "otro" no vale
 *   texto     cómo se enseña cada opción en el desplegable (por defecto, tal cual)
 *   leer      convierte lo escrito en "otro" en un valor (o null si no vale)
 *   El resto de propiedades (placeholder, inputMode...) van al campo de "otro".
 */
import { useState } from "react";

const OTRO = "otro";

export default function SelectorConOtro({ opciones, valor, onChange, texto = String, leer, etiqueta, ...campo }) {
  // Dos estados: si está abierto el campo de "otro" y lo que lleva escrito en él
  const [otro, setOtro] = useState(valor == null);
  const [escrito, setEscrito] = useState("");
  // Por si el valor actual no estuviera entre las opciones: lo añadimos para que no se pierda
  const lista = !otro && valor != null && !opciones.includes(valor) ? [...opciones, valor] : opciones;

  function elegir(e) {
    if (e.target.value === OTRO) {
      setOtro(true);
      onChange(leer(escrito));
    } else {
      setOtro(false);
      onChange(lista[Number(e.target.value)]); // el value de cada <option> es su posición en la lista
    }
  }

  function escribir(e) {
    setEscrito(e.target.value);
    onChange(leer(e.target.value));
  }

  return (
    <>
      <select className="campo" aria-label={etiqueta} value={otro ? OTRO : lista.indexOf(valor)} onChange={elegir}>
        {lista.map((opcion, i) => <option key={i} value={i}>{texto(opcion)}</option>)}
        <option value={OTRO}>Añadir otro…</option>
      </select>
      {otro && (
        <input className="campo" aria-label={`${etiqueta} (otro)`} value={escrito} onChange={escribir}
          autoFocus {...campo} />
      )}
    </>
  );
}
