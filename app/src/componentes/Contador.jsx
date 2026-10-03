// Botones − y + para goles, gpp, el resultado o el importe de una multa.
// `paso`: cuánto suma o resta cada toque. `formato`: cómo se enseña el número (p. ej. 30 -> "0,30 €").
export default function Contador({ valor, onChange, min = 0, max = 30, paso = 1, formato = String, etiqueta,
                                   className = "" }) {
  return (
    <div className={`contador ${className}`} role="group" aria-label={etiqueta}>
      <button type="button" onClick={() => onChange(Math.max(min, valor - paso))} disabled={valor <= min}
        aria-label={`Quitar ${etiqueta}`}>−</button>
      <span aria-live="polite">{formato(valor)}</span>
      <button type="button" onClick={() => onChange(Math.min(max, valor + paso))} disabled={valor >= max}
        aria-label={`Añadir ${etiqueta}`}>+</button>
    </div>
  );
}
