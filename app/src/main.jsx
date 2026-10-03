// Punto de entrada: monta la app de React en <div id="root"> (index.html)
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { HashRouter } from "react-router";

// Fuentes empaquetadas con la app (sin depender de internet ni de un CDN)
import "@fontsource/barlow/latin-400.css";
import "@fontsource/barlow/latin-500.css";
import "@fontsource/barlow/latin-600.css";
import "@fontsource/barlow/latin-700.css";
import "@fontsource/barlow-condensed/latin-600.css";
import "@fontsource/barlow-condensed/latin-700.css";
import "./estilos.css";

import App from "./App";
import { AvisosProvider } from "./avisos";
import Conectando from "./pantallas/Conectando";
import { SesionProvider } from "./sesion";

// HashRouter: las direcciones van tras un # (/#/partidos). El servidor siempre entrega el
// mismo index.html y es React quien decide qué pantalla pintar, así no hay que configurar
// rutas en el servidor.
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
