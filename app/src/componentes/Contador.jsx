// Botones − y + para goles, gpp o el resultado
export default function Contador({ valor, onChange, min = 0, max = 30, etiqueta }) {
  return (
    <div className="contador" role="group" aria-label={etiqueta}>
      <button type="button" onClick={() => onChange(Math.max(min, valor - 1))} disabled={valor <= min}
        aria-label={`Quitar ${etiqueta}`}>−</button>
      <span aria-live="polite">{valor}</span>
      <button type="button" onClick={() => onChange(Math.min(max, valor + 1))} disabled={valor >= max}
        aria-label={`Añadir ${etiqueta}`}>+</button>
    </div>
  );
}
