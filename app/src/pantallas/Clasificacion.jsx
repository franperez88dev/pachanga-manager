// Tabla ordenable. El orden se guarda en la dirección (#/clasificacion?orden=gpp) para que "atrás" lo respete.
import { useNavigate, useSearchParams } from "react-router";
import Avatar from "../componentes/avatar/Avatar";
import { Cargando, MensajeError, Vacio } from "../componentes/Estados";
import { MOSTRAR_ASISTENCIAS } from "../config";
import { useCarga } from "../hooks/useCarga";
import { useSesion } from "../sesion";

const COLUMNAS = [
  { clave: "goles", corto: "G", largo: "Goles" },
  ...(MOSTRAR_ASISTENCIAS ? [{ clave: "asistencias", corto: "A", largo: "Asistencias" }] : []),
  { clave: "gpp", corto: "GPP", largo: "En propia" },
  { clave: "partidos", corto: "PJ", largo: "Partidos" },
];

export default function Clasificacion() {
  const { usuario } = useSesion();
  const navegar = useNavigate();
  const [parametros, setParametros] = useSearchParams();
  const orden = COLUMNAS.some((c) => c.clave === parametros.get("orden")) ? parametros.get("orden") : "goles";
  const { datos, cargando, error, recargar } = useCarga(`/api/clasificacion?orden=${orden}`);

  return (
    <div className="pila">
      <h1 className="titulo-pagina">Clasificación</h1>
      <div className="segmentos" role="tablist" aria-label="Ordenar por">
        {COLUMNAS.map((c) => (
          <button key={c.clave} role="tab" aria-selected={orden === c.clave}
            onClick={() => setParametros({ orden: c.clave }, { replace: true })}>{c.largo}</button>
        ))}
      </div>
      {cargando && !datos ? <Cargando /> : error ? <MensajeError mensaje={error} reintentar={recargar} /> :
        datos.clasificacion.length === 0 ? <Vacio>Aún no hay jugadores.</Vacio> : (
          <table className="tabla">
            <thead>
              <tr>
                <th>#</th>
                <th>Jugador</th>
                {COLUMNAS.map((c) => (
                  <th key={c.clave} className={orden === c.clave ? "activa" : ""} title={c.largo}>
                    <button onClick={() => setParametros({ orden: c.clave }, { replace: true })}>{c.corto}</button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {datos.clasificacion.map((f, i) => (
                <tr key={f.id} className={f.id === usuario.id ? "yo" : ""} onClick={() => navegar(`/jugador/${f.id}`)}>
                  <td className="posicion">{i + 1}</td>
                  <td>
                    <span className="celda-jugador">
                      <Avatar avatar={f.avatar} tam={28} />
                      <span className="nombre">{f.mote}{f.id === usuario.id && " (tú)"}</span>
                    </span>
                  </td>
                  {COLUMNAS.map((c) => (
                    <td key={c.clave} className={`numero ${orden === c.clave ? "activa" : ""}`}>{f[c.clave]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      <p className="nota centrado">Solo cuentan los goles confirmados de partidos ya jugados.</p>
    </div>
  );
}
