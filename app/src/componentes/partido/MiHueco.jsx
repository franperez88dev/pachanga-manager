// La tarjeta de cada jugador en un partido abierto y sin equipos: reservar o liberar su hueco
import { useState } from "react";
import { api } from "../../api";
import { useAvisar } from "../../avisos";
import { plural } from "../../formato";
import BotonConfirmar from "../BotonConfirmar";

export default function MiHueco({ partido, alCambiar }) {
  const avisar = useAvisar();
  const [ocupado, setOcupado] = useState(false);
  const libres = Math.max(partido.plazas - partido.num_apuntados, 0);

  async function reservar() {
    setOcupado(true);
    try {
      const datos = await api.post(`/api/partidos/${partido.id}/hueco`);
      alCambiar(datos.partido);
      avisar(datos.partido.soy_reserva ? `Apuntado de reserva (puesto ${datos.partido.mi_puesto})` : "¡Hueco reservado!");
    } catch (e) {
      avisar(e.message);
    } finally {
      setOcupado(false);
    }
  }

  async function liberar() {
    try {
      const datos = await api.borrar(`/api/partidos/${partido.id}/hueco`);
      alCambiar(datos.partido);
      avisar(datos.multa ? "Hueco liberado. Te llevas una multa por avisar con menos de 24 horas" : "Hueco liberado");
    } catch (e) {
      avisar(e.message);
    }
  }

  // --- Todavía no estoy apuntado
  if (!partido.apuntado) {
    return (
      <div className="tarjeta relleno">
        <div className="mi-hueco">
          <span className="mi-hueco-numero libre" aria-hidden="true">?</span>
          <div>
            <div className="mi-hueco-titulo">{libres > 0 ? "Aún no tienes hueco" : "El partido está lleno"}</div>
            <div className="nota">
              {libres > 0
                ? `${libres === 1 ? "Queda" : "Quedan"} ${plural(libres, "hueco libre", "huecos libres")}.`
                : "Puedes apuntarte de reserva: si alguien se cae, entras por orden."}
            </div>
          </div>
        </div>
        <button className="btn btn-primario btn-ancho" disabled={ocupado} onClick={reservar}>
          {libres > 0 ? "✋ Reservar hueco" : "✋ Apuntarme de reserva"}
        </button>
      </div>
    );
  }

  // --- Estoy apuntado (juego o soy reserva)
  const multa = partido.multa_si_libero;
  return (
    <div className="tarjeta relleno">
      <div className="mi-hueco">
        <span className={`mi-hueco-numero ${partido.soy_reserva ? "reserva" : ""}`}>{partido.mi_puesto}</span>
        <div>
          <div className="mi-hueco-titulo">{partido.soy_reserva ? "Estás de reserva" : "Tienes hueco ✔"}</div>
          <div className="nota">
            {partido.soy_reserva
              ? "Si alguien libera su hueco, entras por orden. Borrarte de reservas no lleva multa."
              : multa
                ? "Si al final no puedes ir, libera tu hueco cuanto antes para que entre otro."
                : "Si no puedes ir, libera tu hueco. Sin multa hasta 24 horas antes del partido."}
          </div>
        </div>
      </div>
      {multa && (
        <div className="banner banner-error">
          ⚠️ Faltan menos de 24 horas: si liberas tu hueco ahora, te llevas una multa (aunque entre un reserva).
        </div>
      )}
      <BotonConfirmar className="btn-ancho" onConfirmar={liberar}
        pregunta={multa ? "¿Seguro? Te llevas una multa" : "¿Seguro? Toca otra vez"}>
        {partido.soy_reserva ? "Salir de reservas" : "Liberar hueco"}
      </BotonConfirmar>
    </div>
  );
}
