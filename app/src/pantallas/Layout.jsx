/*
 * RUTAS: con react-router cada "pantalla" tiene una dirección (#/partidos, #/perfil...).
 * Este Layout es el marco común: cabecera arriba, barra de pestañas abajo, y en medio
 * <Outlet />, que es el hueco donde react-router pinta la pantalla de la ruta actual.
 */
import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";
import { api } from "../api";
import Avatar from "../componentes/avatar/Avatar";
import BotonTema from "../componentes/BotonTema";
import { IconoAdmin, IconoInicio, IconoPartidos, IconoPerfil, IconoTabla, IconoValorar } from "../componentes/Iconos";
import { useSesion } from "../sesion";

function usePendientesAdmin(esAdmin) {
  const { pathname } = useLocation();
  const [pendientes, setPendientes] = useState(0);
  useEffect(() => {
    if (!esAdmin) return;
    let vigente = true;
    // Al cambiar de pantalla, recontamos para el globito rojo: altas, goles por confirmar y
    // multas que un jugador dice haber pagado (solo las que me toca confirmar a mí)
    Promise.all([api.get("/api/admin/altas"), api.get("/api/admin/reportes"), api.get("/api/admin/multas")])
      .then(([a, r, m]) => vigente && setPendientes(
        a.altas.length + r.reportes.length + m.multas.filter((x) => x.aviso_pago && x.me_toca).length))
      .catch(() => {});
    return () => { vigente = false; };
  }, [esAdmin, pathname]);
  return pendientes;
}

export default function Layout() {
  const { usuario } = useSesion();
  const pendientes = usePendientesAdmin(usuario.es_admin);
  const { pathname } = useLocation();

  // Al cambiar de pantalla, volvemos arriba del todo
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);

  const pestanas = [
    { a: "/", texto: "Inicio", icono: <IconoInicio />, fin: true },
    { a: "/partidos", texto: "Partidos", icono: <IconoPartidos /> },
    { a: "/clasificacion", texto: "Tabla", icono: <IconoTabla /> },
    { a: "/valorar", texto: "Valorar", icono: <IconoValorar /> },
    ...(usuario.es_admin ? [{ a: "/admin", texto: "Admin", icono: <IconoAdmin />, globo: pendientes }] : []),
  ];

  return (
    <div className="app">
      <header className="cabecera">
        <Link to="/" className="marca">
          <span className="insignia" aria-hidden="true">⚽</span>
          <span>
            <span className="marca-titulo">Pachanga Manager</span>
            <span className="marca-sub">La peña del fútbol de los amiguetes</span>
          </span>
        </Link>
        <div className="cabecera-derecha">
          <BotonTema />
          <Link to="/perfil" className="mi-avatar" aria-label="Mi perfil">
            <Avatar avatar={usuario.avatar} tam={38} />
          </Link>
        </div>
      </header>
      <main className="contenido">
        <Outlet />
      </main>
      <nav className="barra-inferior" aria-label="Secciones">
        {pestanas.map((p) => (
          <NavLink key={p.a} to={p.a} end={p.fin} className="pestana">
            <span className="pestana-icono">
              {p.icono}
              {p.globo > 0 && <span className="globo">{p.globo}</span>}
            </span>
            <span>{p.texto}</span>
          </NavLink>
        ))}
        <NavLink to="/perfil" className="pestana">
          <span className="pestana-icono"><IconoPerfil /></span>
          <span>Perfil</span>
        </NavLink>
      </nav>
    </div>
  );
}
