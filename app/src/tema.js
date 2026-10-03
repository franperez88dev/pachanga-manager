// Tema claro u oscuro. La elección se guarda en el móvil (localStorage) y se pone en
// <html data-tema="...">; los colores de cada tema están en estilos.css.
// Al abrir la app, quien aplica lo guardado es public/tema.js (antes de que arranque React).
const CLAVE_TEMA = "pachanga.tema";

// El tema que se está viendo ahora: el elegido con el botón o, si no se ha elegido, el del móvil
export function temaActual() {
  const elegido = document.documentElement.dataset.tema;
  if (elegido === "claro" || elegido === "oscuro") return elegido;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "oscuro" : "claro";
}

export function ponerTema(tema) {
  document.documentElement.dataset.tema = tema;
  try { localStorage.setItem(CLAVE_TEMA, tema); } catch { /* sin almacenamiento: vale solo para esta visita */ }
}
