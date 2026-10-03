/*
 * "Conectando con el servidor…": hasta que /health responde no enseñamos nada más.
 * Si el servidor no contesta (sin cobertura, servidor reiniciándose...), reintentamos
 * solos cada pocos segundos.
 */
import { useEffect, useState } from "react";
import { peticion } from "../api";

const ESPERA_ENTRE_INTENTOS = 3000;

export default function Conectando({ children }) {
  const [conectado, setConectado] = useState(false);
  const [intentos, setIntentos] = useState(0);

  useEffect(() => {
    if (conectado) return;
    let vigente = true;
    let temporizador;
    peticion("/health", { timeout: 10000 })
      .then(() => vigente && setConectado(true))
      .catch(() => {
        if (vigente) temporizador = setTimeout(() => setIntentos((n) => n + 1), ESPERA_ENTRE_INTENTOS);
      });
    return () => { vigente = false; clearTimeout(temporizador); };
  }, [intentos, conectado]);

  if (conectado) return children;

  let mensaje = null;
  if (intentos >= 15) mensaje = "No conseguimos conectar. Comprueba que tienes internet. Seguimos intentándolo…";
  else if (intentos >= 2) mensaje = "Está tardando más de lo normal. Seguimos intentándolo…";

  return (
    <div className="pantalla-completa">
      <span className="balon-girando grande" aria-hidden="true">⚽</span>
      <h1 className="titulo-marca">Pachanga Manager</h1>
      <p role="status">Conectando con el servidor…</p>
      {mensaje && <p className="nota">{mensaje}</p>}
      {intentos >= 15 && (
        <button className="btn btn-suave" onClick={() => setIntentos((n) => n + 1)}>Reintentar ahora</button>
      )}
    </div>
  );
}
