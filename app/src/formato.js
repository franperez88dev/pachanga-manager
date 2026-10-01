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
