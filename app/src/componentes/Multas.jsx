// Piezas comunes para enseñar multas (en Mi perfil, en Inicio y en el panel de admin)
import { fechaPartido } from "../formato";

const ESTADOS = {
  pendiente: { texto: "Pendiente", clase: "peligro" },
  pagada: { texto: "Pagada ✔", clase: "confirmado" },
  perdonada: { texto: "Perdonada", clase: "gris" },
};

export function EstadoMulta({ estado }) {
  const { texto, clase } = ESTADOS[estado] ?? ESTADOS.pendiente;
  return <span className={`etiqueta-estado ${clase}`}>{texto}</span>;
}

// "Partido del sáb, 4 oct · 19:00 — Hueco liberado con menos de 24 horas…"
export function TextoMulta({ multa }) {
  return (
    <>
      <div className="fuerte">Partido del {fechaPartido(multa.partido.fecha, true).toLowerCase()}</div>
      <div className="nota nota-larga">{multa.motivo}</div>
    </>
  );
}
