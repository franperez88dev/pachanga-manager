import { Desconocido, ESPECIALES, Persona } from "./dibujos";

/**
 * Avatar redondo de un jugador.
 *   <Avatar avatar={jugador.avatar} tam={40} />
 *   <Avatar avatar={...} camiseta="#1c1c1c" />   (en la pista, con la camiseta del equipo)
 * PROPS: son los "parámetros" de un componente. Se leen como un objeto: aquí desestructurado.
 */
export default function Avatar({ avatar, tam, camiseta = "#0f7a4d", className = "" }) {
  let contenido;
  if (avatar?.tipo === "especial") contenido = (ESPECIALES[avatar.id] ?? Desconocido)();
  else if (avatar?.tipo === "persona") contenido = <Persona a={avatar} camiseta={camiseta} />;
  else contenido = <Desconocido />;

  return (
    <span className={`avatar ${className}`} style={tam ? { width: tam, height: tam } : undefined}>
      <svg viewBox="0 0 100 100" aria-hidden="true">{contenido}</svg>
    </span>
  );
}
