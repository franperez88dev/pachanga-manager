// Entrar (mote + PIN) o registrarse (mote, nombre real opcional y avatar)
import { useEffect, useState } from "react";
import { api, token } from "../api";
import { avatarAleatorio, avatarParaEnviar } from "../componentes/avatar/aleatorio";
import EditorAvatar from "../componentes/avatar/EditorAvatar";
import { Cargando, MensajeError } from "../componentes/Estados";
import { useCatalogoAvatares } from "../hooks/useCatalogoAvatares";
import { useSesion } from "../sesion";

function FormularioEntrar() {
  const { entrar } = useSesion();
  const [mote, setMote] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(e) {
    e.preventDefault(); // un <form> recarga la página al enviarse; así lo evitamos
    setError(null);
    setEnviando(true);
    try {
      const datos = await api.post("/api/auth/login", { mote, pin });
      entrar(datos.token, datos.usuario);
    } catch (err) {
      setError(err.message);
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} className="formulario">
      <label className="campo-etiqueta">
        Tu mote
        <input className="campo" value={mote} onChange={(e) => setMote(e.target.value)} placeholder="Ej: Feragi"
          autoComplete="username" autoCapitalize="words" required />
      </label>
      <label className="campo-etiqueta">
        Tu PIN
        <input className="campo campo-pin" value={pin} type="password" inputMode="numeric" maxLength={4}
          pattern="[0-9]{4}" placeholder="••••" autoComplete="current-password" required
          onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))} />
      </label>
      {error && <p className="error-formulario" role="alert">{error}</p>}
      <button className="btn btn-primario btn-ancho" disabled={enviando || !mote.trim() || pin.length !== 4}>Entrar</button>
      <p className="nota centrado">¿Has olvidado tu PIN? Pídele uno nuevo al admin.</p>
    </form>
  );
}

function FormularioRegistro({ alRegistrarse }) {
  const { catalogo, error: errorCatalogo } = useCatalogoAvatares();
  const [mote, setMote] = useState("");
  const [nombreReal, setNombreReal] = useState("");
  const [avatar, setAvatar] = useState(null);
  const [error, setError] = useState(null);
  const [enviando, setEnviando] = useState(false);

  // En cuanto llega el catálogo, empezamos con un avatar al azar
  useEffect(() => {
    if (catalogo && !avatar) setAvatar(avatarAleatorio(catalogo));
  }, [catalogo, avatar]);

  async function enviar(e) {
    e.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      const datos = await api.post("/api/auth/registro",
        { mote, nombre_real: nombreReal, avatar: avatarParaEnviar(avatar) });
      alRegistrarse(datos);
    } catch (err) {
      setError(err.message);
      setEnviando(false);
    }
  }

  if (errorCatalogo) return <MensajeError mensaje={errorCatalogo} />;
  if (!catalogo || !avatar) return <Cargando />;

  return (
    <form onSubmit={enviar} className="formulario">
      <label className="campo-etiqueta">
        Tu mote en la pachanga
        <input className="campo" value={mote} onChange={(e) => setMote(e.target.value)} placeholder="Ej: El Muro"
          maxLength={20} autoCapitalize="words" required />
      </label>
      <label className="campo-etiqueta">
        <span>Nombre real <small>(opcional)</small></span>
        <input className="campo" value={nombreReal} onChange={(e) => setNombreReal(e.target.value)}
          placeholder="Ej: Fernando" maxLength={60} autoComplete="given-name" />
      </label>
      <div className="campo-etiqueta">Tu avatar</div>
      <EditorAvatar catalogo={catalogo} valor={avatar} onChange={setAvatar} />
      {error && <p className="error-formulario" role="alert">{error}</p>}
      <button className="btn btn-primario btn-ancho" disabled={enviando || mote.trim().length < 2}>Unirme a la peña</button>
    </form>
  );
}

function PinAsignado({ datos, alContinuar }) {
  return (
    <div className="tarjeta relleno pin-asignado">
      <div className="etiqueta">Tu PIN para entrar</div>
      <div className="pin-grande" aria-label={`PIN ${datos.pin.split("").join(" ")}`}>{datos.pin}</div>
      <p>
        Apúntalo, <b>{datos.usuario.mote}</b>. Entrarás siempre con tu <b>mote + este PIN</b>.
        No se lo digas a nadie y guárdalo bien: <b>no se puede volver a consultar</b>{" "}
        (si lo olvidas, el admin te dará uno nuevo).
      </p>
      <p className="nota">Tu dorsal en la peña es el <b>{String(datos.usuario.dorsal).padStart(2, "0")}</b>.</p>
      <button className="btn btn-primario btn-ancho" onClick={alContinuar}>Lo he apuntado</button>
    </div>
  );
}

export default function Entrar() {
  const { entrar } = useSesion();
  const [pestana, setPestana] = useState("entrar");
  const [registro, setRegistro] = useState(null);

  function alRegistrarse(datos) {
    // Guardamos ya el token (por si se cierra la app), pero primero enseñamos el PIN
    token.guardar(datos.token);
    setRegistro(datos);
  }

  return (
    <div className="pantalla-acceso">
      <div className="acceso-cabecera">
        <span className="insignia grande" aria-hidden="true">⚽</span>
        <h1 className="titulo-marca">Pachanga Manager</h1>
        <p className="nota">La peña del fútbol de los amiguetes</p>
      </div>
      {registro ? (
        <PinAsignado datos={registro} alContinuar={() => entrar(registro.token, registro.usuario)} />
      ) : (
        <div className="tarjeta relleno">
          <div className="segmentos" role="tablist">
            <button role="tab" aria-selected={pestana === "entrar"} onClick={() => setPestana("entrar")}>Ya estoy en la peña</button>
            <button role="tab" aria-selected={pestana === "registro"} onClick={() => setPestana("registro")}>Soy nuevo</button>
          </div>
          {pestana === "entrar" ? <FormularioEntrar /> : <FormularioRegistro alRegistrarse={alRegistrarse} />}
        </div>
      )}
    </div>
  );
}
