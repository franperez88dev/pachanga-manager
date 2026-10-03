// Pequeñas utilidades para mostrar datos en español

const fechaLarga = new Intl.DateTimeFormat("es-ES", { weekday: "long", day: "numeric", month: "long" });
const fechaCorta = new Intl.DateTimeFormat("es-ES", { weekday: "short", day: "numeric", month: "short" });
const hora = new Intl.DateTimeFormat("es-ES", { hour: "2-digit", minute: "2-digit" });

// El backend manda la fecha del partido sin zona ("2026-10-04T19:00"): es la hora de aquí
export function fechaPartido(iso, corta = false) {
  const d = new Date(iso);
  const dia = (corta ? fechaCorta : fechaLarga).format(d);
  return `${dia.charAt(0).toUpperCase()}${dia.slice(1)} · ${hora.format(d)}`;
}

// 14.5 -> "14,5"
export function decimal(numero) {
  return numero.toFixed(1).replace(".", ",");
}

export function plural(n, singular, plural = `${singular}s`) {
  return `${n} ${n === 1 ? singular : plural}`;
}

// --- Dinero. El servidor lo manda siempre en céntimos (220 = 2,20 €) para no tener líos con los decimales

// Precio de un partido, como se escribe en el grupo: 220 -> "2,2"   300 -> "3"   225 -> "2,25"
export function precio(centimos) {
  return String(centimos / 100).replace(".", ",");
}

// Importe de una multa, con sus dos decimales: 30 -> "0,30 €"
export function dinero(centimos) {
  return `${(centimos / 100).toFixed(2).replace(".", ",")} €`;
}

// Lo que escribe el admin ("2,5" o "2.5") -> céntimos (250). Si no es un precio válido, null.
export function leerPrecio(texto) {
  const limpio = texto.trim().replace(",", ".");
  const euros = Number(limpio);
  if (limpio === "" || !Number.isFinite(euros) || euros < 0 || euros > 100) return null;
  return Math.round(euros * 100);
}
