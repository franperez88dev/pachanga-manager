// Mensajitos flotantes ("Valoración enviada", "Guardado"...). Otro contexto, como el de la sesión.
import { createContext, useCallback, useContext, useRef, useState } from "react";

const AvisosContext = createContext(() => {});

export function AvisosProvider({ children }) {
  const [texto, setTexto] = useState(null);
  const temporizador = useRef(null); // useRef: guarda un valor entre repintados sin provocar uno nuevo

  const avisar = useCallback((mensaje) => {
    setTexto(mensaje);
    clearTimeout(temporizador.current);
    temporizador.current = setTimeout(() => setTexto(null), 2600);
  }, []);

  return (
    <AvisosContext.Provider value={avisar}>
      {children}
      <div className={`aviso-flotante ${texto ? "visible" : ""}`} role="status" aria-live="polite">{texto}</div>
    </AvisosContext.Provider>
  );
}

export function useAvisar() {
  return useContext(AvisosContext);
}
