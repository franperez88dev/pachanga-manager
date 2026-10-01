/*
 * COMPONENTE CONTROLADO: el editor no guarda el avatar elegido; lo recibe del padre
 * (prop `valor`) y le avisa de cada cambio (prop `onChange`). Así el padre (registro
 * o perfil) siempre sabe qué avatar hay y puede enviarlo al backend.
 */
import { useState } from "react";
import Avatar from "./Avatar";
import { avatarAleatorio, personaAleatoria } from "./aleatorio";

const NOMBRE_PEINADO = { calvo: "Calvo", corto: "Corto", tupe: "Tupé", rizos: "Rizos", melena: "Melena", cresta: "Cresta" };
const NOMBRE_BARBA = { ninguna: "Sin barba", bigote: "Bigote", perilla: "Perilla", completa: "Completa" };

export default function EditorAvatar({ catalogo, valor, onChange }) {
  // Si eliges un especial y luego tocas el peinado, recuperamos el último muñeco que tenías
  const [ultimaPersona, setUltimaPersona] = useState(() =>
    valor.tipo === "persona" ? valor : personaAleatoria(catalogo));

  function cambiarCampo(campo, opcion) {
    const base = valor.tipo === "persona" ? valor : ultimaPersona;
    const nuevo = { ...base, [campo]: opcion };
    setUltimaPersona(nuevo);
    onChange(nuevo);
  }

  function aleatorio() {
    const nuevo = avatarAleatorio(catalogo);
    if (nuevo.tipo === "persona") setUltimaPersona(nuevo);
    onChange(nuevo);
  }

  const marcado = (campo, opcion) => valor.tipo === "persona" && valor[campo] === opcion;

  const filaChips = (titulo, campo, opciones, nombres) => (
    <div className="editor-fila">
      <div className="etiqueta">{titulo}</div>
      <div className="chips">
        {opciones.map((o) => (
          <button key={o} type="button" className="chip" aria-pressed={marcado(campo, o)} onClick={() => cambiarCampo(campo, o)}>
            {nombres[o] ?? o}
          </button>
        ))}
      </div>
    </div>
  );

  const filaColores = (titulo, campo, colores) => (
    <div className="editor-fila">
      <div className="etiqueta">{titulo}</div>
      <div className="chips">
        {colores.map((c) => (
          <button key={c} type="button" className="muestra-color" style={{ background: c }} aria-label={`Color ${c}`}
            aria-pressed={marcado(campo, c)} onClick={() => cambiarCampo(campo, c)} />
        ))}
      </div>
    </div>
  );

  return (
    <div className="editor-avatar">
      <div className="editor-vista">
        <Avatar avatar={valor} tam={124} className="avatar-grande" />
        <button type="button" className="btn btn-primario" onClick={aleatorio}>🎲 Aleatorio</button>
      </div>
      {filaColores("Piel", "piel", catalogo.pieles)}
      {filaChips("Peinado", "peinado", catalogo.peinados, NOMBRE_PEINADO)}
      {filaColores("Color del pelo", "color_pelo", catalogo.colores_pelo)}
      {filaChips("Barba", "barba", catalogo.barbas, NOMBRE_BARBA)}
      {valor.tipo === "persona" && valor.barba !== "ninguna" &&
        filaColores("Color de la barba", "color_barba", catalogo.colores_pelo)}
      <div className="editor-fila">
        <div className="etiqueta">O un avatar especial</div>
        <div className="especiales">
          {catalogo.especiales.map((e) => (
            <button key={e.id} type="button" className="especial" title={e.nombre} aria-label={e.nombre}
              aria-pressed={valor.tipo === "especial" && valor.id === e.id}
              onClick={() => onChange({ tipo: "especial", id: e.id })}>
              <Avatar avatar={{ tipo: "especial", id: e.id }} tam={54} />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
