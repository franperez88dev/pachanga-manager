// Avatar al azar con las opciones del catálogo (GET /api/avatares)

const elegir = (lista) => lista[Math.floor(Math.random() * lista.length)];
const COLORES_NATURALES = 8; // los primeros colores de pelo; los últimos (azul, rosa) son "raros"

export function avatarAleatorio(catalogo) {
  if (catalogo.especiales.length && Math.random() < 0.2) {
    // 1 de cada 5: sorpresa (alien, perro... o uno subido por un admin)
    const e = elegir(catalogo.especiales);
    return { tipo: "especial", id: e.id, ...(e.imagen ? { imagen: e.imagen } : {}) };
  }
  return personaAleatoria(catalogo);
}

export function personaAleatoria(catalogo) {
  const raros = Math.random() < 0.1;
  const pelo = elegir(raros ? catalogo.colores_pelo : catalogo.colores_pelo.slice(0, COLORES_NATURALES));
  return {
    tipo: "persona",
    piel: elegir(catalogo.pieles),
    peinado: elegir(catalogo.peinados),
    color_pelo: pelo,
    barba: elegir(catalogo.barbas),
    color_barba: pelo,
  };
}

// Lo que se manda al backend (la ruta de la imagen la pone él)
export function avatarParaEnviar(avatar) {
  if (avatar.tipo === "especial") return { tipo: "especial", id: avatar.id };
  const { tipo, piel, peinado, color_pelo, barba, color_barba } = avatar;
  return { tipo, piel, peinado, color_pelo, barba, color_barba };
}
