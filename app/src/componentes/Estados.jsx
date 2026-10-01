// Estados comunes de cualquier pantalla: cargando, error y "no hay nada"

export function Cargando({ texto = "Cargando…" }) {
  return (
    <div className="estado" role="status">
      <span className="balon-girando" aria-hidden="true">⚽</span>
      <span>{texto}</span>
    </div>
  );
}

export function MensajeError({ mensaje, reintentar }) {
  return (
    <div className="estado estado-error" role="alert">
      <span>{mensaje}</span>
      {reintentar && <button className="btn btn-suave" onClick={reintentar}>Reintentar</button>}
    </div>
  );
}

export function Vacio({ children }) {
  return <div className="estado">{children}</div>;
}
