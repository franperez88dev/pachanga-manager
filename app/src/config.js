import escudoNevados from "./assets/escudos/nevados.png";
import escudoSombras from "./assets/escudos/sombras.png";

// URL del backend: sale de VITE_API_URL (.env.development en local, .env.production en el APK final)
export const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

// De momento solo llevamos goles (ver DECISIONES.md). Poner a true para recuperar las asistencias.
export const MOSTRAR_ASISTENCIAS = false;

export const EQUIPOS = {
  blanco: { nombre: "Nevados C.F.", escudo: escudoNevados, camiseta: "#f4f4f4" },
  negro: { nombre: "Sombras F.C.", escudo: escudoSombras, camiseta: "#1c1c1c" },
};
