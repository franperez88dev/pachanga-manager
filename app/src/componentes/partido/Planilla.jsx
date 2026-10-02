/*
 * Planilla del admin al cerrar el partido: primero goles y gpp de cada jugador (+/-),
 * "Confirmar"; después las asistencias (si están activadas). "Sig." se la salta y deja
 * que cada jugador apunte lo suyo desde su móvil.
 */
import { useEffect, useState } from "react";
import { api } from "../../api";
import { useAvisar } from "../../avisos";
import { EQUIPOS, MOSTRAR_ASISTENCIAS } from "../../config";
import Avatar from "../avatar/Avatar";
import Contador from "../Contador";
import { Cargando, MensajeError } from "../Estados";

const PASOS = [
  { titulo: "Goles", campos: [["goles", "Goles"], ["gpp", "GPP"]] },
  ...(MOSTRAR_ASISTENCIAS ? [{ titulo: "Asistencias", campos: [["asistencias", "Asist."]] }] : []),
];

// Mismo cálculo que el backend (servicios.exceso_marcador y avisos_marcador), para avisar mientras se edita.
//  - errores: algún equipo tiene MÁS goles que el resultado -> no se puede confirmar
//  - avisos: faltan goles (se pueden apuntar más tarde) -> se puede confirmar igualmente
function revisarMarcador(jugadores, valores, resultado) {
  const rival = { blanco: "negro", negro: "blanco" };
  const marcador = { blanco: 0, negro: 0 };
  const golesPropios = { blanco: 0, negro: 0 };
  const asistencias = { blanco: 0, negro: 0 };
  for (const j of jugadores) {
    const v = valores[j.id];
    marcador[j.equipo] += v.goles;
    marcador[rival[j.equipo]] += v.gpp;
    golesPropios[j.equipo] += v.goles;
    asistencias[j.equipo] += v.asistencias;
  }
  const errores = [];
  const avisos = [];
  for (const color of ["blanco", "negro"]) {
    if (marcador[color] > resultado[color]) {
      errores.push(`${EQUIPOS[color].nombre}: hay ${marcador[color]} goles apuntados (con los gpp del rival) y el resultado es ${resultado[color]}. Quita ${marcador[color] - resultado[color]}.`);
    } else if (marcador[color] < resultado[color]) {
      avisos.push(`${EQUIPOS[color].nombre}: faltan ${resultado[color] - marcador[color]} por apuntar (hay ${marcador[color]} de ${resultado[color]}).`);
    }
    if (MOSTRAR_ASISTENCIAS && asistencias[color] > golesPropios[color]) {
      avisos.push(`${EQUIPOS[color].nombre}: hay más asistencias que goles.`);
    }
  }
  return { errores, avisos };
}

export default function Planilla({ partido, alTerminar }) {
  const avisar = useAvisar();
  const [planilla, setPlanilla] = useState(null);
  const [error, setError] = useState(null);
  const [valores, setValores] = useState({});
  const [paso, setPaso] = useState(0);
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    api.get(`/api/partidos/${partido.id}/estadisticas`)
      .then((datos) => {
        setPlanilla(datos);
        // Se precarga con lo confirmado + lo que cada jugador tenga pendiente
        const inicial = {};
        for (const j of datos.jugadores) {
          const p = j.pendiente ?? { goles: 0, gpp: 0, asistencias: 0 };
          inicial[j.id] = { goles: j.goles + p.goles, gpp: j.gpp + p.gpp, asistencias: j.asistencias + p.asistencias };
        }
        setValores(inicial);
      })
      .catch((e) => setError(e.message));
  }, [partido.id]);

  if (error) return <MensajeError mensaje={error} />;
  if (!planilla) return <Cargando />;

  const { errores, avisos } = revisarMarcador(planilla.jugadores, valores, planilla.resultado);
  const { titulo, campos } = PASOS[paso];
  const cambiar = (id, campo, v) => setValores({ ...valores, [id]: { ...valores[id], [campo]: v } });

  async function confirmar() {
    if (paso < PASOS.length - 1) {
      setPaso(paso + 1);
      return;
    }
    setGuardando(true);
    try {
      const filas = planilla.jugadores.map((j) => ({ id: j.id, ...valores[j.id] }));
      await api.put(`/api/partidos/${partido.id}/estadisticas`, { jugadores: filas });
      avisar("Goles guardados");
      alTerminar(true);
    } catch (e) {
      avisar(e.message);
      setGuardando(false);
    }
  }

  return (
    <section className="tarjeta relleno">
      <div className="planilla-cabecera">
        <h3 className="titulo-tarjeta">{titulo}</h3>
        <span className="nota">Resultado: {planilla.resultado.blanco}–{planilla.resultado.negro}</span>
      </div>
      {["blanco", "negro"].map((color) => (
        <div key={color} className="planilla-equipo">
          <div className={`planilla-equipo-titulo ${color}`}>
            <span className="nombre">{EQUIPOS[color].nombre}</span>
            {campos.map(([campo, etiqueta]) => <span key={campo} className="columna">{etiqueta}</span>)}
          </div>
          {planilla.jugadores.filter((j) => j.equipo === color).map((j) => (
            <div key={j.id} className="planilla-fila">
              <Avatar avatar={j.avatar} tam={28} />
              <span className="nombre">{j.mote}</span>
              {campos.map(([campo, etiqueta]) => (
                <Contador key={campo} valor={valores[j.id][campo]} etiqueta={`${etiqueta} de ${j.mote}`}
                  onChange={(v) => cambiar(j.id, campo, v)} />
              ))}
            </div>
          ))}
        </div>
      ))}
      {errores.length > 0 && (
        <div className="banner banner-error" role="alert">
          {errores.map((e) => <p key={e}>⛔ {e}</p>)}
          <p>No puede haber más goles que en el resultado.</p>
        </div>
      )}
      {errores.length === 0 && avisos.length > 0 && (
        <div className="banner">
          {avisos.map((a) => <p key={a}>⚠️ {a}</p>)}
          <p>Puedes guardar igualmente y apuntar el resto más tarde.</p>
        </div>
      )}
      <div className="acciones">
        {paso === 0
          ? <button className="btn btn-suave" onClick={() => alTerminar(false)} title="Que cada uno apunte lo suyo">Sig. ›</button>
          : <button className="btn btn-suave" onClick={() => setPaso(paso - 1)}>‹ Atrás</button>}
        <button className="btn btn-primario" disabled={guardando || errores.length > 0} onClick={confirmar}>Confirmar</button>
      </div>
    </section>
  );
}
