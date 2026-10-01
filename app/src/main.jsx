// Punto de entrada: monta la app de React en <div id="root"> (index.html)
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { HashRouter } from "react-router";

// Fuentes empaquetadas con la app (sin depender de internet ni de un CDN)
import "@fontsource/barlow/400.css";
import "@fontsource/barlow/500.css";
import "@fontsource/barlow/600.css";
import "@fontsource/barlow/700.css";
import "@fontsource/barlow-condensed/600.css";
import "@fontsource/barlow-condensed/700.css";
import "./estilos.css";

import App from "./App";
import { AvisosProvider } from "./avisos";
import Conectando from "./pantallas/Conectando";
import { SesionProvider } from "./sesion";

// HashRouter: las direcciones van tras un # (index.html#/partidos). Funciona dentro de
// Capacitor sin configurar nada en un servidor, porque el archivo siempre es index.html.
createRoot(document.getElementById("root")).render(
  <StrictMode>
    <HashRouter>
      <AvisosProvider>
        <Conectando>
          <SesionProvider>
            <App />
          </SesionProvider>
        </Conectando>
      </AvisosProvider>
    </HashRouter>
  </StrictMode>,
);
