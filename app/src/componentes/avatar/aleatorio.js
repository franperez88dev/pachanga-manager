// Avatar al azar con las opciones del catálogo (GET /api/avatares)

const elegir = (lista) => lista[Math.floor(Math.random() * lista.length)];
const COLORES_NATURALES = 8; // los primeros colores de pelo; los últimos (azul, rosa) son "raros"

export function avatarAleatorio(catalogo) {
  if (catalogo.especiales.length && Math.random() < 0.2) {
    // 1 de cada 5: sorpresa (alien, perro, gato...)
    return { tipo: "especial", id: elegir(catalogo.especiales).id };
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

// Lo que se manda al backend: solo los campos que conoce
export function avatarParaEnviar(avatar) {
  if (avatar.tipo === "especial") return { tipo: "especial", id: avatar.id };
  const { tipo, piel, peinado, color_pelo, barba, color_barba } = avatar;
  return { tipo, piel, peinado, color_pelo, barba, color_barba };
}
