// Panel de admin con sub-pestañas (rutas anidadas: #/admin/altas, #/admin/goles...)
import { useRef, useState } from "react";
import { NavLink, Outlet } from "react-router";
import { api } from "../api";
import { useAvisar } from "../avisos";
import Avatar from "../componentes/avatar/Avatar";
import BotonConfirmar from "../componentes/BotonConfirmar";
import Contador from "../componentes/Contador";
import { Cargando, MensajeError, Vacio } from "../componentes/Estados";
import { EstadoMulta } from "../componentes/Multas";
import { MOSTRAR_ASISTENCIAS } from "../config";
import { dinero, fechaPartido, plural } from "../formato";
import { useCarga } from "../hooks/useCarga";
import { useSesion } from "../sesion";

export default function Admin() {
  return (
    <div className="pila">
      <h1 className="titulo-pagina">Panel de admin</h1>
      <nav className="segmentos" aria-label="Secciones del panel">
        <NavLink to="altas">Altas</NavLink>
        <NavLink to="goles">Goles</NavLink>
        <NavLink to="multas">Multas</NavLink>
        <NavLink to="pena">Peña</NavLink>
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

export function MultasAdmin() {
  const avisar = useAvisar();
  const carga = useCarga("/api/admin/multas");
  // useRef guarda un valor que sobrevive entre repintados SIN provocar uno nuevo. Aquí, la "cola"
  // de envíos: si tocas + varias veces seguidas, cada cambio espera a que termine el anterior.
  const cola = useRef(Promise.resolve());

  async function poner(multa, estado) {
    try {
      await api.put(`/api/admin/multas/${multa.id}`, { estado });
      avisar({ pagada: "Multa pagada ✔", perdonada: "Multa perdonada", pendiente: "Vuelve a estar pendiente" }[estado]);
      carga.recargar();
    } catch (e) {
      avisar(e.message);
    }
  }

  function cambiarImporte(multa, importe) {
    // Primero se cambia en pantalla (para que el botón responda al momento) y luego se guarda
    carga.poner({ multas: carga.datos.multas.map((m) => (m.id === multa.id ? { ...m, importe_centimos: importe } : m)) });
    cola.current = cola.current
      .then(() => api.put(`/api/admin/multas/${multa.id}`, { importe_centimos: importe }))
      .catch((e) => { avisar(e.message); carga.recargar(); });
  }

  const fila = (m) => (
    <div key={m.id} className="fila-lista fila-pena">
      <Avatar avatar={m.jugador.avatar} tam={42} />
      <div className="fila-lista-texto">
        <div className="fuerte">{m.jugador.mote} <EstadoMulta estado={m.estado} /></div>
        <div className="nota">Partido del {fechaPartido(m.partido.fecha, true).toLowerCase()}</div>
        <div className="nota nota-larga">{m.motivo}</div>
        {m.estado !== "pendiente" && m.importe_centimos > 0 && <div className="nota">Importe: {dinero(m.importe_centimos)}</div>}
      </div>
      {m.estado === "pendiente" && m.aviso_pago && (
        <div className="banner banner-verde aviso-pago">
          💬 <b>{m.jugador.mote}</b> dice que ya la ha pagado.{" "}
          {m.me_toca ? "Si es así, pulsa «Pagada»." : `Le toca confirmarlo a ${m.cobrador}.`}
        </div>
      )}
      {m.estado === "pendiente" ? (
        <div className="multa-pie">
          <Contador className="contador-dinero" valor={m.importe_centimos} paso={10} max={10000} formato={dinero}
            etiqueta={`10 céntimos a la multa de ${m.jugador.mote}`} onChange={(importe) => cambiarImporte(m, importe)} />
          <div className="acciones-fila">
            <BotonConfirmar peligro={false} pregunta="¿Perdonarla?" onConfirmar={() => poner(m, "perdonada")}>Perdonar</BotonConfirmar>
            <button className="btn btn-primario" onClick={() => poner(m, "pagada")}>Pagada</button>
          </div>
        </div>
      ) : (
        <div className="acciones-fila">
          <button className="btn btn-suave" onClick={() => poner(m, "pendiente")}>Deshacer</button>
        </div>
      )}
    </div>
  );

  return (
    <ConDatos carga={carga}>
      {({ multas }) => {
        if (multas.length === 0) return <Vacio>Nadie tiene multas. ¡Qué peña más formal! 👏</Vacio>;
        // Arriba, las que alguien dice haber pagado y me toca confirmar a mí
        const urgente = (m) => (m.aviso_pago && m.me_toca ? 0 : 1);
        const pendientes = multas.filter((m) => m.estado === "pendiente").sort((x, y) => urgente(x) - urgente(y));
        const resueltas = multas.filter((m) => m.estado !== "pendiente");
        return (
          <div className="lista">
            <p className="nota">
              Se ponen solas cuando alguien libera su hueco con menos de 24 horas, o cuando quitas a alguien "con multa".
              Con − y + pones el importe (de 10 en 10 céntimos) y lo vas subiendo si pasan los días sin pagar.
            </p>
            {pendientes.length === 0 && <p className="nota centrado">No hay ninguna pendiente 👌</p>}
            {pendientes.map(fila)}
            {resueltas.length > 0 && <h2 className="titulo-seccion">Ya resueltas</h2>}
            {resueltas.map(fila)}
          </div>
        );
      }}
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
