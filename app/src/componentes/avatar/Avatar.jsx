import { API_URL } from "../../config";
import { Desconocido, ESPECIALES, Persona } from "./dibujos";

/**
 * Avatar redondo de un jugador.
 *   <Avatar avatar={jugador.avatar} tam={40} />
 *   <Avatar avatar={...} camiseta="#1c1c1c" />   (en la pista, con la camiseta del equipo)
 * PROPS: son los "parámetros" de un componente. Se leen como un objeto: aquí desestructurado.
 */
export default function Avatar({ avatar, tam, camiseta = "#0f7a4d", className = "" }) {
  const estilo = tam ? { width: tam, height: tam } : undefined;
  let contenido;
  if (avatar?.imagen) {
    // Imagen subida por un admin
    return (
      <span className={`avatar ${className}`} style={estilo}>
        <img src={API_URL + avatar.imagen} alt="" loading="lazy" />
      </span>
    );
  } else if (avatar?.tipo === "especial") {
    contenido = (ESPECIALES[avatar.id] ?? Desconocido)();
  } else if (avatar?.tipo === "persona") {
    contenido = <Persona a={avatar} camiseta={camiseta} />;
  } else {
    contenido = <Desconocido />;
  }
  return (
    <span className={`avatar ${className}`} style={estilo}>
      <svg viewBox="0 0 100 100" aria-hidden="true">{contenido}</svg>
    </span>
  );
}
