import { Navigate, Route, Routes } from "react-router";
import { Cargando, MensajeError } from "./componentes/Estados";
import Admin, { Altas, AvataresAdmin, GolesPendientes, Pena } from "./pantallas/Admin";
import Clasificacion from "./pantallas/Clasificacion";
import Entrar from "./pantallas/Entrar";
import EsperaAprobacion from "./pantallas/EsperaAprobacion";
import Inicio from "./pantallas/Inicio";
import Layout from "./pantallas/Layout";
import PaginaPartido from "./pantallas/PaginaPartido";
import Partidos from "./pantallas/Partidos";
import { MiPerfil, PerfilJugador } from "./pantallas/Perfil";
import { ListaValorar, ValorarJugador } from "./pantallas/Valorar";
import { useSesion } from "./sesion";

export default function App() {
  const { usuario, comprobando, errorInicial, reintentar } = useSesion();

  if (comprobando) return <div className="pantalla-completa"><Cargando texto="Entrando…" /></div>;
  if (errorInicial) return <div className="pantalla-completa"><MensajeError mensaje={errorInicial} reintentar={reintentar} /></div>;
  if (!usuario) return <Entrar />;
  if (usuario.estado !== "aprobado") return <EsperaAprobacion />;

  // Cada <Route> asocia una dirección con una pantalla. Las de dentro de "Layout" se pintan en su <Outlet />.
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Inicio />} />
        <Route path="partidos" element={<Partidos />} />
        <Route path="partidos/:id" element={<PaginaPartido />} />
        <Route path="clasificacion" element={<Clasificacion />} />
        <Route path="valorar" element={<ListaValorar />} />
        <Route path="valorar/:id" element={<ValorarJugador />} />
        <Route path="perfil" element={<MiPerfil />} />
        <Route path="jugador/:id" element={<PerfilJugador />} />
        {usuario.es_admin && (
          <Route path="admin" element={<Admin />}>
            <Route index element={<Navigate to="altas" replace />} />
            <Route path="altas" element={<Altas />} />
            <Route path="goles" element={<GolesPendientes />} />
            <Route path="pena" element={<Pena />} />
            <Route path="avatares" element={<AvataresAdmin />} />
          </Route>
        )}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
