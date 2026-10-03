// Botón del sol / la luna: cambia entre tema claro y oscuro
import { useState } from "react";
import { ponerTema, temaActual } from "../tema";
import { IconoLuna, IconoSol } from "./Iconos";

export default function BotonTema({ className = "" }) {
  // El estado solo sirve para que React repinte el icono: el tema de verdad vive en <html data-tema>
  const [tema, setTema] = useState(temaActual);
  const otro = tema === "oscuro" ? "claro" : "oscuro";

  function cambiar() {
    ponerTema(otro);
    setTema(otro);
  }

  return (
    <button type="button" className={`boton-tema ${className}`} onClick={cambiar}
      aria-label={`Cambiar a tema ${otro}`} title={`Cambiar a tema ${otro}`}>
      {/* Se enseña el icono del tema al que vas a cambiar */}
      {tema === "oscuro" ? <IconoSol /> : <IconoLuna />}
    </button>
  );
}
