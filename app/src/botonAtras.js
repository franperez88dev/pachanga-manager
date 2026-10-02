// Botón "atrás" de Android (solo dentro del APK; en el navegador no hace nada).
// - En una pantalla interior: vuelve a la anterior, como el "atrás" del navegador.
// - En Inicio: cierra la app (la deja en segundo plano), como cualquier app de Android.
import { App } from "@capacitor/app";
import { Capacitor } from "@capacitor/core";

export function activarBotonAtras() {
  if (!Capacitor.isNativePlatform()) return;
  App.addListener("backButton", ({ canGoBack }) => {
    const enInicio = window.location.hash === "" || window.location.hash === "#/";
    if (enInicio) App.exitApp();
    else if (canGoBack) window.history.back();
    else window.location.hash = "#/";
  });
}
