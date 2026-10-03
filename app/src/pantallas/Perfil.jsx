// /perfil (el mío: cambiar avatar, salir, borrar cuenta) y /jugador/:id (el de otro)
import { useState } from "react";
import { useNavigate, useParams } from "react-router";
import { api } from "../api";
import { useAvisar } from "../avisos";
import { avatarParaEnviar } from "../componentes/avatar/aleatorio";
import Avatar from "../componentes/avatar/Avatar";
import EditorAvatar from "../componentes/avatar/EditorAvatar";
import BotonConfirmar from "../componentes/BotonConfirmar";
import { Cargando, MensajeError } from "../componentes/Estados";
import { EstadoMulta, TextoMulta } from "../componentes/Multas";
import { MOSTRAR_ASISTENCIAS } from "../config";
import { useCarga } from "../hooks/useCarga";
import { useCatalogoAvatares } from "../hooks/useCatalogoAvatares";
import { useSesion } from "../sesion";

function Ficha({ jugador }) {
  const datos = [
    ["Goles", jugador.goles],
    ...(MOSTRAR_ASISTENCIAS ? [["Asistencias", jugador.asistencias]] : []),
    ["En propia", jugador.gpp],
    ["Partidos", jugador.partidos],
  ];
  return (
    <div className="tarjeta relleno centrado ficha-jugador">
      <div className="ficha-avatar-grande">
        <Avatar avatar={jugador.avatar} tam={110} className="avatar-grande" />
        <span className="ficha-dorsal grande">{jugador.dorsal}</span>
      </div>
      <div className="nombre-grande">
        {jugador.mote} {jugador.es_admin && <span className="etiqueta-admin">Admin</span>}
      </div>
      {jugador.nombre_real && <div className="nota">{jugador.nombre_real}</div>}
      <div className="estadisticas">
        {datos.map(([texto, valor]) => (
          <div key={texto}><span className="numero-grande">{valor}</span><span className="nota">{texto}</span></div>
        ))}
      </div>
    </div>
  );
}

function CambiarAvatar({ alTerminar }) {
  const { usuario, setUsuario } = useSesion();
  const avisar = useAvisar();
  const { catalogo, error } = useCatalogoAvatares();
  const [avatar, setAvatar] = useState(usuario.avatar);
  const [guardando, setGuardando] = useState(false);

  if (error) return <MensajeError mensaje={error} />;
  if (!catalogo) return <Cargando />;

  async function guardar() {
    setGuardando(true);
    try {
      const datos = await api.put("/api/yo/avatar", { avatar: avatarParaEnviar(avatar) });
      setUsuario(datos.usuario);
      avisar("Avatar cambiado");
      alTerminar(true);
    } catch (e) {
      avisar(e.message);
      setGuardando(false);
    }
  }

  return (
    <div className="tarjeta relleno">
      <EditorAvatar catalogo={catalogo} valor={avatar} onChange={setAvatar} />
      <div className="acciones">
        <button className="btn btn-suave" onClick={() => alTerminar(false)}>Cancelar</button>
        <button className="btn btn-primario" disabled={guardando} onClick={guardar}>Guardar avatar</button>
      </div>
    </div>
  );
}

// Solo aparece si tienes (o has tenido) alguna multa. Nadie más ve las tuyas, salvo el admin.
function MisMultas() {
  const { datos } = useCarga("/api/multas/mias");
  if (!datos || datos.multas.length === 0) return null;
  return (
    <section id="multas">
      <h2 className="titulo-seccion">Mis multas</h2>
      <div className="lista">
        {datos.multas.map((m) => (
          <div key={m.id} className="fila-lista">
            <div className="fila-lista-texto"><TextoMulta multa={m} /></div>
            <EstadoMulta estado={m.estado} />
          </div>
        ))}
      </div>
      <p className="nota">Cuando la pagues, el admin la marcará como pagada.</p>
    </section>
  );
}

export function MiPerfil() {
  const { usuario, salir } = useSesion();
  const avisar = useAvisar();
  const ficha = useCarga(`/api/jugadores/${usuario.id}`);
  const [editando, setEditando] = useState(false);

  async function borrarCuenta() {
    try {
      await api.borrar("/api/yo", { confirmar: true });
      avisar("Cuenta borrada. ¡Hasta otra!");
      salir();
    } catch (e) {
      avisar(e.message);
    }
  }

  return (
    <div className="pila">
      <h1 className="titulo-pagina">Mi perfil</h1>
      {ficha.cargando && !ficha.datos ? <Cargando /> : ficha.error
        ? <MensajeError mensaje={ficha.error} reintentar={ficha.recargar} />
        : <Ficha jugador={{ ...ficha.datos.jugador, avatar: usuario.avatar }} />}
      {editando
        ? <CambiarAvatar alTerminar={() => setEditando(false)} />
        : <button className="btn btn-suave btn-ancho" onClick={() => setEditando(true)}>🎨 Cambiar avatar</button>}
      <MisMultas />
      <button className="btn btn-suave btn-ancho" onClick={salir}>Cerrar sesión</button>
      <section className="zona-peligro">
        <h2 className="titulo-seccion">Borrar mi cuenta</h2>
        <p className="nota">
          Se borran para siempre tu cuenta, tus valoraciones, tus goles, tus multas y tus huecos en los partidos. No se puede deshacer.
        </p>
        <BotonConfirmar pregunta="¿Seguro? Toca otra vez para borrar" onConfirmar={borrarCuenta} className="btn-ancho">
          Borrar mi cuenta
        </BotonConfirmar>
      </section>
      {/* __VERSION__ lo rellena Vite al compilar (vite.config.js) */}
      <p className="nota centrado">Pachanga Manager · versión {__VERSION__}</p>
    </div>
  );
}

export function PerfilJugador() {
  const { id } = useParams();
  const navegar = useNavigate();
  const { datos, cargando, error, recargar } = useCarga(`/api/jugadores/${id}`);
  return (
    <div className="pila">
      {/* navegar(-1) = como el botón "atrás": vuelve a la pista, la tabla... de donde vinieras */}
      <button className="volver" onClick={() => navegar(-1)}>‹ Volver</button>
      {cargando && !datos ? <Cargando /> : error ? <MensajeError mensaje={error} reintentar={recargar} />
        : <Ficha jugador={datos.jugador} />}
    </div>
  );
}
