// Lista de compañeros para valorar (en secreto, una vez) y la ficha con las estrellas
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { api } from "../api";
import { useAvisar } from "../avisos";
import Avatar from "../componentes/avatar/Avatar";
import { Cargando, MensajeError, Vacio } from "../componentes/Estados";
import Estrellas from "../componentes/Estrellas";
import { useCarga } from "../hooks/useCarga";
import { useSesion } from "../sesion";

export function ListaValorar() {
  const { usuario } = useSesion();
  const jugadores = useCarga("/api/jugadores");
  const mias = useCarga("/api/valoraciones/mias");

  if ((jugadores.cargando && !jugadores.datos) || (mias.cargando && !mias.datos)) return <Cargando />;
  const error = jugadores.error || mias.error;
  if (error) return <MensajeError mensaje={error} reintentar={() => { jugadores.recargar(); mias.recargar(); }} />;

  const valorados = new Set(mias.datos.valorados);
  const otros = jugadores.datos.jugadores.filter((j) => j.id !== usuario.id);
  const pendientes = otros.filter((j) => !valorados.has(j.id)).length;

  return (
    <div className="pila">
      <h1 className="titulo-pagina">Valorar compañeros</h1>
      <p className="nota">
        Dale de 1 a 5 estrellas a la calidad de cada compañero. Solo <b>una vez</b> y es <b>secreto</b>:
        nadie ve la nota de nadie. Sirve para hacer equipos igualados.
        {pendientes > 0 && <> Te quedan <b>{pendientes}</b> por valorar.</>}
      </p>
      {otros.length === 0 ? <Vacio>Todavía no hay compañeros que valorar.</Vacio> : (
        <div className="lista">
          {otros.map((j) => (
            <Link key={j.id} to={`/valorar/${j.id}`} className="fila-lista">
              <Avatar avatar={j.avatar} tam={42} />
              <div className="fila-lista-texto">
                <div className="fuerte">{j.mote}</div>
                {j.nombre_real && <div className="nota">{j.nombre_real}</div>}
              </div>
              {valorados.has(j.id)
                ? <span className="etiqueta-estado confirmado">Valorado ✓</span>
                : <span className="btn btn-suave btn-pequeno">Valorar ›</span>}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export function ValorarJugador() {
  const { id } = useParams();
  const avisar = useAvisar();
  const navegar = useNavigate();
  const jugador = useCarga(`/api/jugadores/${id}`);
  const mias = useCarga("/api/valoraciones/mias");
  const [estrellas, setEstrellas] = useState(0);
  const [enviando, setEnviando] = useState(false);

  if ((jugador.cargando && !jugador.datos) || (mias.cargando && !mias.datos)) return <Cargando />;
  if (jugador.error || mias.error) return <MensajeError mensaje={jugador.error || mias.error} />;

  const j = jugador.datos.jugador;
  const yaValorado = mias.datos.valorados.includes(j.id);

  async function enviar() {
    setEnviando(true);
    try {
      await api.post("/api/valoraciones", { valorado_id: j.id, estrellas });
      avisar(`Valoración de ${j.mote} enviada (secreta)`);
      navegar("/valorar");
    } catch (e) {
      avisar(e.message);
      setEnviando(false);
    }
  }

  return (
    <div className="pila">
      <Link to="/valorar" className="volver">‹ Valorar</Link>
      <div className="tarjeta relleno centrado ficha-valorar">
        <Avatar avatar={j.avatar} tam={96} className="avatar-grande" />
        <div className="nombre-grande">{j.mote}</div>
        {j.nombre_real && <div className="nota">{j.nombre_real}</div>}
        <hr />
        {yaValorado ? (
          <p className="nota">🔒 Ya valoraste a {j.mote}. No se puede cambiar ni volver a ver.</p>
        ) : (
          <>
            <div className="titulo-seccion">Su calidad como jugador</div>
            <Estrellas valor={estrellas} onChange={setEstrellas} />
            <button className="btn btn-primario" disabled={!estrellas || enviando} onClick={enviar}>Enviar valoración</button>
            <p className="nota">Una vez enviada no se puede cambiar.</p>
          </>
        )}
        <p className="nota-secreta">🔒 Las notas individuales son invisibles para todos (también para el admin).
          Solo se usan para equilibrar los equipos.</p>
      </div>
    </div>
  );
}
