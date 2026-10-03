// Todo lo de un partido, según su estado y según quién lo mire (admin, jugador, reserva o no apuntado)
import { useState } from "react";
import { useNavigate } from "react-router";
import { api } from "../../api";
import { useAvisar } from "../../avisos";
import { EQUIPOS } from "../../config";
import { decimal, fechaPartido } from "../../formato";
import { useSesion } from "../../sesion";
import BotonConfirmar from "../BotonConfirmar";
import CerrarPartido from "./CerrarPartido";
import FormularioPartido from "./FormularioPartido";
import ListaApuntados from "./ListaApuntados";
import MiHueco from "./MiHueco";
import MisGoles from "./MisGoles";
import OrdenPorteria from "./OrdenPorteria";
import Pista from "./Pista";
import Planilla from "./Planilla";
import Votacion, { BarraVotos } from "./Votacion";

function Cabecera({ partido }) {
  return (
    <div className="tarjeta cabecera-partido">
      <div>
        <div className="fecha-partido">{fechaPartido(partido.fecha)}</div>
        <div className="lugar-partido">📍 {partido.lugar}</div>
      </div>
      <span className={`chip-estado ${partido.estado}`}>{partido.estado === "abierto" ? "Próximo" : "Jugado"}</span>
    </div>
  );
}

// El texto libre que escribe el admin: cuánto cuesta y a quién se le paga
function Precio({ partido }) {
  if (!partido.info_pago) return null;
  return <div className="banner precio"><span aria-hidden="true">💶</span><span>{partido.info_pago}</span></div>;
}

// "Juegas con…" en los colores del equipo y con su escudo grande
function TuEquipo({ color, pasado = false }) {
  return (
    <div className={`tu-equipo ${color}`}>
      <img src={EQUIPOS[color].escudo} alt="" />
      <div>
        <div className="tu-equipo-texto">{pasado ? "Jugaste con" : "Juegas con"}</div>
        <div className="tu-equipo-nombre">{EQUIPOS[color].nombre}</div>
      </div>
    </div>
  );
}

export function Resultado({ partido }) {
  const { blanco, negro } = partido.resultado;
  return (
    <div className="tarjeta resultado">
      <div className="resultado-lado"><img src={EQUIPOS.blanco.escudo} alt="" /><span>{EQUIPOS.blanco.nombre}</span></div>
      <div className="resultado-goles">{blanco}<span>–</span>{negro}</div>
      <div className="resultado-lado"><img src={EQUIPOS.negro.escudo} alt="" /><span>{EQUIPOS.negro.nombre}</span></div>
    </div>
  );
}

// Admin, antes de hacer los equipos: crear equipos (cuando estén los 10) y editar el partido
function AdminSinEquipos({ partido, alCambiar, alEditar }) {
  const avisar = useAvisar();
  const [ocupado, setOcupado] = useState(false);
  const juegan = Math.min(partido.num_apuntados, partido.plazas);
  const completo = juegan === partido.plazas;

  async function crearEquipos() {
    setOcupado(true);
    try {
      const datos = await api.post(`/api/partidos/${partido.id}/equipos`, {});
      alCambiar(datos.partido);
      avisar("¡Equipos hechos!");
    } catch (e) {
      avisar(e.message);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <div className="tarjeta relleno">
      <span className="etiqueta-admin">Admin</span>
      <p className="nota">
        {completo
          ? "Ya están los 10. Al crear los equipos la lista se cierra: los jugadores ya no podrán apuntarse ni borrarse."
          : `Para crear los equipos hacen falta 10 apuntados (hay ${juegan}).`}
      </p>
      <button className="btn btn-primario btn-ancho" disabled={!completo || ocupado} onClick={crearEquipos}>
        ⚙️ Crear equipos (Blanco vs Negro)
      </button>
      <button className="btn btn-suave btn-ancho" onClick={alEditar}>✏️ Editar día, lugar o precio</button>
    </div>
  );
}

function ControlesAdmin({ partido, alCambiar, alEditar, alCerrar }) {
  const avisar = useAvisar();
  const [ocupado, setOcupado] = useState(false);
  const v = partido.votacion;

  async function rebarajar() {
    setOcupado(true);
    try {
      const datos = await api.post(`/api/partidos/${partido.id}/equipos`, { rebarajar: true });
      alCambiar(datos.partido);
      avisar("¡Nuevos equipos!");
    } catch (e) {
      avisar(e.message);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <div className="tarjeta relleno">
      <span className="etiqueta-admin">Admin</span>
      {v.abierta ? (
        <>
          <p className="nota">
            {v.se_puede_rebarajar
              ? `¡${v.votos_si} votos a favor! Ya puedes rebarajar (reparto ${v.repartos_hechos + 1} de ${v.repartos_maximos}).`
              : `Rebarajar se activa con ${v.votos_necesarios} votos a favor de los que juegan.`}
          </p>
          {/* Si el admin juega, ya ve el recuento en su tarjeta de votar */}
          {!partido.convocado && <BarraVotos votacion={v} />}
        </>
      ) : (
        <p className="nota">Repartos agotados ({v.repartos_hechos} de {v.repartos_maximos}).</p>
      )}
      <div className="acciones">
        <button className="btn btn-suave" onClick={alEditar}>✏️ Editar</button>
        <button className="btn btn-primario" disabled={!v.se_puede_rebarajar || ocupado} onClick={rebarajar}>↻ Rebarajar</button>
      </div>
      <button className="btn btn-oscuro btn-ancho" onClick={alCerrar}>🏁 Cerrar partido</button>
      <p className="nota">Si alguien no puede ir, quítalo en la lista de abajo: entra el primer reserva y se rehacen los equipos.</p>
    </div>
  );
}

export default function VistaPartido({ partido, alCambiar }) {
  const { usuario } = useSesion();
  const avisar = useAvisar();
  const navegar = useNavigate();
  const esAdmin = usuario.es_admin;
  // Qué panel del admin está abierto: null, "editar", "cerrar" o "planilla"
  const [panel, setPanel] = useState(null);
  const [planillaSaltada, setPlanillaSaltada] = useState(false);

  async function borrarPartido() {
    try {
      await api.borrar(`/api/partidos/${partido.id}`);
      avisar("Partido borrado");
      navegar("/partidos");
    } catch (e) {
      avisar(e.message);
    }
  }

  const equipos = partido.equipos;

  if (partido.estado === "abierto") {
    const editor = esAdmin && panel === "editar" && (
      <FormularioPartido partido={partido} alCancelar={() => setPanel(null)}
        alGuardar={(p) => { alCambiar(p); setPanel(null); avisar("Partido actualizado"); }} />
    );
    return (
      <div className="pila">
        <Cabecera partido={partido} />
        <Precio partido={partido} />
        {!equipos ? (
          <>
            <MiHueco partido={partido} alCambiar={alCambiar} />
            <ListaApuntados partido={partido} alCambiar={alCambiar} gestionar={esAdmin} />
            {editor}
            {esAdmin && panel !== "editar" && (
              <AdminSinEquipos partido={partido} alCambiar={alCambiar} alEditar={() => setPanel("editar")} />
            )}
          </>
        ) : (
          <>
            {partido.convocado && <TuEquipo color={partido.mi_equipo} />}
            {partido.soy_reserva && (
              <div className="banner">
                Estás de reserva (puesto {partido.mi_puesto}). Los equipos ya están hechos: si alguien se cae, el admin te avisará.
              </div>
            )}
            {!partido.apuntado && <div className="banner">No juegas este partido: los equipos ya están hechos y la lista está cerrada.</div>}
            <Pista equipos={equipos} />
            <p className="nota centrado">Diferencia de fuerza: <b>{decimal(equipos.diferencia)} pts</b></p>
            {partido.convocado && <Votacion partido={partido} alCambiar={alCambiar} />}
            {partido.convocado && (
              <p className="nota centrado">La lista está cerrada. Si no puedes ir, avisa al admin.</p>
            )}
            {editor}
            {esAdmin && panel === "cerrar" && (
              <CerrarPartido partido={partido} alCancelar={() => setPanel(null)}
                alCambiar={(p) => { alCambiar(p); setPanel("planilla"); }} />
            )}
            {esAdmin && panel === null && (
              <ControlesAdmin partido={partido} alCambiar={alCambiar}
                alEditar={() => setPanel("editar")} alCerrar={() => setPanel("cerrar")} />
            )}
            <OrdenPorteria equipos={equipos} />
            {/* Los 10 ya se ven en la pista: la lista solo hace falta si hay reservas o para que el admin la gestione */}
            {(esAdmin || partido.num_reservas > 0) && (
              <ListaApuntados partido={partido} alCambiar={alCambiar} gestionar={esAdmin} />
            )}
          </>
        )}
        {esAdmin && (
          <BotonConfirmar pregunta="¿Seguro? Se borra el partido" onConfirmar={borrarPartido} className="btn-ancho">
            Borrar partido
          </BotonConfirmar>
        )}
      </div>
    );
  }

  // Partido cerrado
  return (
    <div className="pila">
      <Cabecera partido={partido} />
      <Resultado partido={partido} />
      {partido.convocado && partido.mi_equipo && <TuEquipo color={partido.mi_equipo} pasado />}
      {esAdmin && panel === "planilla" && (
        <Planilla partido={partido} alTerminar={(guardada) => { setPanel(null); setPlanillaSaltada(!guardada); }} />
      )}
      {esAdmin && panel !== "planilla" && (
        <div className="tarjeta relleno">
          <span className="etiqueta-admin">Admin</span>
          {planillaSaltada && (
            <p className="nota">Cada jugador puede apuntar sus goles desde su móvil. Te llegarán al panel de admin para confirmarlos.</p>
          )}
          <button className="btn btn-primario btn-ancho" onClick={() => setPanel("planilla")}>📝 Apuntar goles del partido</button>
        </div>
      )}
      {partido.convocado && <MisGoles partido={partido} />}
      {equipos && <Pista equipos={equipos} />}
    </div>
  );
}
