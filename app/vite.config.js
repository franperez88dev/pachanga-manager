import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite: el servidor de desarrollo (npm run dev) y el empaquetador (npm run build -> dist/)
export default defineConfig({
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5173 },
});
