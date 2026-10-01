// Botón de doble confirmación: el primer toque pregunta "¿Seguro?", el segundo ejecuta.
// Si no se confirma en unos segundos, vuelve a su estado normal.
import { useEffect, useState } from "react";

export default function BotonConfirmar({ children, pregunta = "¿Seguro?", onConfirmar, peligro = true,
                                         className = "", disabled = false }) {
  const [armado, setArmado] = useState(false);
  const [ocupado, setOcupado] = useState(false);

  useEffect(() => {
    if (!armado) return;
    const t = setTimeout(() => setArmado(false), 4000);
    return () => clearTimeout(t); // "limpieza" del efecto: si se desmonta antes, se cancela el temporizador
  }, [armado]);

  async function pulsar() {
    if (!armado) {
      setArmado(true);
      return;
    }
    setArmado(false);
    setOcupado(true);
    try {
      await onConfirmar();
    } finally {
      setOcupado(false);
    }
  }

  const clase = peligro ? "btn-peligro" : "btn-suave";
  return (
    <button type="button" className={`btn ${clase} ${armado ? "armado" : ""} ${className}`}
      onClick={pulsar} disabled={disabled || ocupado}>
      {armado ? pregunta : children}
    </button>
  );
}
