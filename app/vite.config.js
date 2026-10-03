import { readFileSync } from "node:fs";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const { version } = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf8"));

// Vite: el servidor de desarrollo (npm run dev) y el empaquetador (npm run build).
export default defineConfig({
  plugins: [react()],
  // __VERSION__ se sustituye al compilar por la versión de package.json (se enseña en el Perfil)
  define: { __VERSION__: JSON.stringify(version) },
  server: { host: "127.0.0.1", port: 5173 },
  build: {
    // La web compilada se deja DENTRO del backend: Flask la sirve tal cual, tanto en tu PC
    // como en PythonAnywhere (allí no hay Node: solo se hace "git pull").
    outDir: "../backend/pachanga/web",
    emptyOutDir: true, // borra la compilación anterior (hace falta decirlo porque está fuera de app/)
  },
});
