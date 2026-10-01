// De 1 a 5 estrellas. Sin `onChange` es solo de lectura.
const RUTA = "M12 3.2l2.6 5.5 6 .7-4.5 4.1 1.2 6-5.3-3-5.3 3 1.2-6L3.4 9.4l6-.7z";

export default function Estrellas({ valor, onChange }) {
  return (
    <div className="estrellas" role={onChange ? "radiogroup" : undefined} aria-label="Valoración">
      {[1, 2, 3, 4, 5].map((n) => {
        const dibujo = (
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d={RUTA} className={n <= valor ? "estrella-llena" : "estrella-vacia"} />
          </svg>
        );
        return onChange ? (
          <button key={n} type="button" role="radio" aria-checked={valor === n} aria-label={`${n} estrellas`}
            onClick={() => onChange(n)}>{dibujo}</button>
        ) : <span key={n}>{dibujo}</span>;
      })}
    </div>
  );
}
