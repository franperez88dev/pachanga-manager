// Mientras el admin no apruebe el alta, solo se ve esto (comprobamos solos cada 20 segundos)
import { useEffect, useState } from "react";
import Avatar from "../componentes/avatar/Avatar";
import { useSesion } from "../sesion";

export default function EsperaAprobacion() {
  const { usuario, recargarUsuario, salir } = useSesion();
  const [comprobando, setComprobando] = useState(false);

  useEffect(() => {
    const intervalo = setInterval(() => { recargarUsuario().catch(() => {}); }, 20000);
    return () => clearInterval(intervalo);
  }, [recargarUsuario]);

  async function comprobarAhora() {
    setComprobando(true);
    try { await recargarUsuario(); } catch { /* sin conexión: se reintenta solo */ } finally { setComprobando(false); }
  }

  return (
    <div className="pantalla-completa">
      <Avatar avatar={usuario.avatar} tam={110} className="avatar-grande" />
      <h1 className="titulo-marca">¡Hola, {usuario.mote}!</h1>
      <p>Esperando aprobación del admin.</p>
      <p className="nota">Cuando te apruebe, entrarás solo. Si tarda, avísale por WhatsApp.</p>
      <button className="btn btn-primario" disabled={comprobando} onClick={comprobarAhora}>Comprobar ahora</button>
      <button className="btn btn-suave" onClick={salir}>Salir</button>
    </div>
  );
}
