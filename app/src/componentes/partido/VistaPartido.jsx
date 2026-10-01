// Todo lo de un partido, según su estado y según quién lo mire (admin, convocado o no)
import { useState } from "react";
import { useNavigate } from "react-router";
import { api } from "../../api";
import { useAvisar } from "../../avisos";
import { EQUIPOS } from "../../config";
import { decimal, fechaPartido } from "../../formato";
import { useSesion } from "../../sesion";
import BotonConfirmar from "../BotonConfirmar";
import CerrarPartido from "./CerrarPartido";
import Convocatoria from "./Convocatoria";
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

function ControlesAdmin({ partido, alCambiar, alVolverAElegir, alCerrar }) {
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
              : `Rebarajar se activa con ${v.votos_necesarios} votos a favor de los convocados.`}
          </p>
          {/* Si el admin está convocado, ya ve el recuento en su tarjeta de votar */}
          {!partido.convocado && <BarraVotos votacion={v} />}
        </>
      ) : (
        <p className="nota">Repartos agotados ({v.repartos_hechos} de {v.repartos_maximos}).</p>
      )}
      <div className="acciones">
        <button className="btn btn-suave" onClick={alVolverAElegir}>‹ Volver a elegir</button>
        <button className="btn btn-primario" disabled={!v.se_puede_rebarajar || ocupado} onClick={rebarajar}>↻ Rebarajar</button>
      </div>
      <button className="btn btn-oscuro btn-ancho" onClick={alCerrar}>🏁 Cerrar partido</button>
    </div>
  );
}

export default function VistaPartido({ partido, alCambiar }) {
  const { usuario } = useSesion();
  const avisar = useAvisar();
  const navegar = useNavigate();
  const esAdmin = usuario.es_admin;
  // Qué panel del admin está abierto: null, "convocatoria", "cerrar" o "planilla"
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
    const verConvocatoria = esAdmin && (!partido.equipos_generados || panel === "convocatoria");
    return (
      <div className="pila">
        <Cabecera partido={partido} />
        {verConvocatoria ? (
          <Convocatoria partido={partido} alCambiar={alCambiar} alTerminar={() => setPanel(null)} />
        ) : !equipos ? (
          <div className="banner">
            {partido.convocado ? "Estás convocado ✔ · " : ""}Los equipos todavía no están hechos.
          </div>
        ) : (
          <>
            {!partido.convocado && <div className="banner">No estás convocado para este partido.</div>}
            {partido.convocado && (
              <div className="banner banner-verde">
                Juegas con <b>{EQUIPOS[partido.mi_equipo].nombre}</b>
              </div>
            )}
            <Pista equipos={equipos} />
            <p className="nota centrado">Diferencia de fuerza: <b>{decimal(equipos.diferencia)} pts</b></p>
            {partido.convocado && <Votacion partido={partido} alCambiar={alCambiar} />}
            {esAdmin && panel === "cerrar" && (
              <CerrarPartido partido={partido} alCancelar={() => setPanel(null)}
                alCambiar={(p) => { alCambiar(p); setPanel("planilla"); }} />
            )}
            {esAdmin && panel !== "cerrar" && (
              <ControlesAdmin partido={partido} alCambiar={alCambiar}
                alVolverAElegir={() => setPanel("convocatoria")} alCerrar={() => setPanel("cerrar")} />
            )}
            <OrdenPorteria equipos={equipos} />
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
      {esAdmin && panel === "planilla" && (
        <Planilla partido={partido} alTerminar={(guardada) => { setPanel(null); setPlanillaSaltada(!guardada); }} />
      )}
      {esAdmin && panel !== "planilla" && (
        <div className="tarjeta relleno">
          <span className="etiqueta-admin">Admin</span>
          {planillaSaltada && (
            <p className="nota">Cada convocado puede apuntar sus goles desde su móvil. Te llegarán al panel de admin para confirmarlos.</p>
          )}
          <button className="btn btn-primario btn-ancho" onClick={() => setPanel("planilla")}>📝 Apuntar goles del partido</button>
        </div>
      )}
      {partido.convocado && <MisGoles partido={partido} />}
      {equipos && <Pista equipos={equipos} />}
    </div>
  );
}
