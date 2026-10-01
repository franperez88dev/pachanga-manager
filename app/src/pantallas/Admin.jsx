// Panel de admin con sub-pestañas (rutas anidadas: #/admin/altas, #/admin/goles...)
import { useState } from "react";
import { NavLink, Outlet } from "react-router";
import { api } from "../api";
import { useAvisar } from "../avisos";
import Avatar from "../componentes/avatar/Avatar";
import BotonConfirmar from "../componentes/BotonConfirmar";
import { Cargando, MensajeError, Vacio } from "../componentes/Estados";
import { MOSTRAR_ASISTENCIAS } from "../config";
import { fechaPartido, plural } from "../formato";
import { useCarga } from "../hooks/useCarga";
import { olvidarCatalogo, useCatalogoAvatares } from "../hooks/useCatalogoAvatares";
import { useSesion } from "../sesion";

export default function Admin() {
  return (
    <div className="pila">
      <h1 className="titulo-pagina">Panel de admin</h1>
      <nav className="segmentos" aria-label="Secciones del panel">
        <NavLink to="altas">Altas</NavLink>
        <NavLink to="goles">Goles</NavLink>
        <NavLink to="pena">Peña</NavLink>
        <NavLink to="avatares">Avatares</NavLink>
      </nav>
      <Outlet />
    </div>
  );
}

// Envoltorio común: cargando / error / contenido
function ConDatos({ carga, children }) {
  if (carga.cargando && !carga.datos) return <Cargando />;
  if (carga.error) return <MensajeError mensaje={carga.error} reintentar={carga.recargar} />;
  return children(carga.datos);
}

export function Altas() {
  const avisar = useAvisar();
  const carga = useCarga("/api/admin/altas");

  async function resolver(u, accion) {
    try {
      await api.post(`/api/admin/usuarios/${u.id}/${accion}`);
      avisar(accion === "aprobar" ? `${u.mote} aprobado ✔` : `${u.mote} rechazado`);
      carga.recargar();
    } catch (e) {
      avisar(e.message);
    }
  }

  return (
    <ConDatos carga={carga}>
      {({ altas }) => altas.length === 0 ? <Vacio>No hay altas pendientes. Cuando alguien se registre, aparecerá aquí.</Vacio> : (
        <div className="lista">
          <p className="nota">Comprueba que son de la peña antes de aprobarlos.</p>
          {altas.map((u) => (
            <div key={u.id} className="fila-lista">
              <Avatar avatar={u.avatar} tam={42} />
              <div className="fila-lista-texto">
                <div className="fuerte">{u.mote}</div>
                <div className="nota">{u.nombre_real || "Sin nombre real"} · dorsal {u.dorsal}</div>
              </div>
              <div className="acciones-fila">
                <BotonConfirmar pregunta="¿Seguro?" onConfirmar={() => resolver(u, "rechazar")}>No</BotonConfirmar>
                <button className="btn btn-primario" onClick={() => resolver(u, "aprobar")}>Aprobar</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </ConDatos>
  );
}

export function GolesPendientes() {
  const avisar = useAvisar();
  const carga = useCarga("/api/admin/reportes");

  async function resolver(r, accion) {
    try {
      await api.post(`/api/admin/reportes/${r.id}/${accion}`);
      avisar(accion === "confirmar" ? `Confirmado lo de ${r.jugador.mote}` : `Descartado lo de ${r.jugador.mote}`);
      carga.recargar();
    } catch (e) {
      avisar(e.message);
    }
  }

  return (
    <ConDatos carga={carga}>
      {({ reportes }) => reportes.length === 0 ? <Vacio>Nada pendiente. Todo al día 👌</Vacio> : (
        <div className="lista">
          <p className="nota">Lo que han apuntado los jugadores. Solo cuenta en la clasificación lo que confirmes.</p>
          {reportes.map((r) => (
            <div key={r.id} className="fila-lista">
              <Avatar avatar={r.jugador.avatar} tam={42} />
              <div className="fila-lista-texto">
                <div className="fuerte">{r.jugador.mote}</div>
                <div className="nota">{fechaPartido(r.partido.fecha, true)}</div>
                <div className="etiquetas">
                  {r.goles > 0 && <span className="etiqueta-estado pendiente">+{plural(r.goles, "gol", "goles")}</span>}
                  {r.gpp > 0 && <span className="etiqueta-estado pendiente">+{r.gpp} gpp</span>}
                  {MOSTRAR_ASISTENCIAS && r.asistencias > 0 && <span className="etiqueta-estado pendiente">+{r.asistencias} asist.</span>}
                </div>
              </div>
              <div className="acciones-fila">
                <BotonConfirmar pregunta="¿Seguro?" onConfirmar={() => resolver(r, "descartar")}>Descartar</BotonConfirmar>
                <button className="btn btn-primario" onClick={() => resolver(r, "confirmar")}>Confirmar</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </ConDatos>
  );
}

export function Pena() {
  const { usuario } = useSesion();
  const avisar = useAvisar();
  const carga = useCarga("/api/admin/usuarios");
  const [pinNuevo, setPinNuevo] = useState(null);

  async function cambiarRol(u) {
    try {
      await api.put(`/api/admin/usuarios/${u.id}/rol`, { rol: u.es_admin ? "jugador" : "admin" });
      avisar(u.es_admin ? `${u.mote} ya no es admin` : `${u.mote} ahora es admin`);
      carga.recargar();
    } catch (e) {
      avisar(e.message);
    }
  }

  async function generarPin(u) {
    try {
      setPinNuevo(await api.post(`/api/admin/usuarios/${u.id}/pin`));
    } catch (e) {
      avisar(e.message);
    }
  }

  return (
    <>
      {pinNuevo && (
        <div className="tarjeta relleno centrado pin-asignado">
          <div className="etiqueta">PIN nuevo de {pinNuevo.mote}</div>
          <div className="pin-grande">{pinNuevo.pin}</div>
          <p className="nota">Pásaselo por WhatsApp. No se podrá volver a ver. Sus sesiones abiertas se han cerrado.</p>
          <button className="btn btn-primario" onClick={() => setPinNuevo(null)}>Hecho</button>
        </div>
      )}
      <ConDatos carga={carga}>
        {({ usuarios }) => (
          <div className="lista">
            <p className="nota">Puedes hacer admin a otro jugador para que gestione contigo. Siempre tiene que quedar uno.</p>
            {usuarios.map((u) => (
              <div key={u.id} className="fila-lista fila-pena">
                <Avatar avatar={u.avatar} tam={42} />
                <div className="fila-lista-texto">
                  <div className="fuerte">{u.mote} {u.es_admin && <span className="etiqueta-admin">Admin</span>}</div>
                  <div className="nota">Dorsal {u.dorsal}{u.nombre_real ? ` · ${u.nombre_real}` : ""}</div>
                </div>
                <div className="acciones-fila">
                  <BotonConfirmar peligro={false} pregunta="¿PIN nuevo?" onConfirmar={() => generarPin(u)}>PIN nuevo</BotonConfirmar>
                  {u.id !== usuario.id && (
                    <BotonConfirmar peligro={u.es_admin} pregunta="¿Seguro?" onConfirmar={() => cambiarRol(u)}>
                      {u.es_admin ? "Quitar admin" : "Hacer admin"}
                    </BotonConfirmar>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </ConDatos>
    </>
  );
}

export function AvataresAdmin() {
  const avisar = useAvisar();
  const [version, setVersion] = useState(0);
  return <ListaAvatares key={version} avisar={avisar} alCambiar={() => { olvidarCatalogo(); setVersion((v) => v + 1); }} />;
}

function ListaAvatares({ avisar, alCambiar }) {
  const { catalogo, error } = useCatalogoAvatares();
  const [nombre, setNombre] = useState("");
  const [fichero, setFichero] = useState(null);
  const [subiendo, setSubiendo] = useState(false);

  if (error) return <MensajeError mensaje={error} />;
  if (!catalogo) return <Cargando />;
  const subidos = catalogo.especiales.filter((e) => e.imagen);

  async function subir(e) {
    e.preventDefault();
    const formulario = new FormData();
    formulario.append("nombre", nombre);
    formulario.append("imagen", fichero);
    setSubiendo(true);
    try {
      await api.subir("/api/admin/avatares", formulario);
      avisar(`Avatar "${nombre}" añadido`);
      alCambiar();
    } catch (err) {
      avisar(err.message);
      setSubiendo(false);
    }
  }

  async function retirar(a) {
    try {
      await api.borrar(`/api/admin/avatares/${a.imagen.split("/").pop()}`);
      avisar(`"${a.nombre}" retirado`);
      alCambiar();
    } catch (err) {
      avisar(err.message);
    }
  }

  return (
    <div className="pila">
      <form className="tarjeta relleno formulario" onSubmit={subir}>
        <h3 className="titulo-tarjeta">Añadir un avatar</h3>
        <p className="nota">Imagen cuadrada PNG, JPEG o WebP de 300 KB como mucho. Aparecerá entre los avatares especiales.</p>
        <label className="campo-etiqueta">
          Nombre
          <input className="campo" value={nombre} onChange={(e) => setNombre(e.target.value)} maxLength={30} required />
        </label>
        <label className="campo-etiqueta">
          Imagen
          <input className="campo" type="file" accept="image/png,image/jpeg,image/webp" required
            onChange={(e) => setFichero(e.target.files[0] ?? null)} />
        </label>
        <button className="btn btn-primario btn-ancho" disabled={subiendo || !nombre.trim() || !fichero}>Subir avatar</button>
      </form>
      <h2 className="titulo-seccion">Avatares subidos</h2>
      {subidos.length === 0 ? <Vacio>Todavía no has subido ninguno.</Vacio> : (
        <div className="lista">
          {subidos.map((a) => (
            <div key={a.id} className="fila-lista">
              <Avatar avatar={a} tam={46} />
              <div className="fila-lista-texto fuerte">{a.nombre}</div>
              <BotonConfirmar pregunta="¿Retirar?" onConfirmar={() => retirar(a)}>Retirar</BotonConfirmar>
            </div>
          ))}
          <p className="nota">Al retirar uno, desaparece del catálogo, pero quien ya lo tenga lo conserva.</p>
        </div>
      )}
    </div>
  );
}
