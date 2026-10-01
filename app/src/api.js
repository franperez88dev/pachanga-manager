// Todas las llamadas al backend pasan por aquí: añade el token, convierte a JSON
// y traduce los errores a mensajes que se pueden enseñar tal cual.
import { API_URL } from "./config";

const CLAVE_TOKEN = "pachanga.token";

// localStorage puede fallar (modo privado, almacenamiento lleno...): nunca dejamos que rompa la app
export const token = {
  leer() {
    try { return localStorage.getItem(CLAVE_TOKEN); } catch { return null; }
  },
  guardar(valor) {
    try { localStorage.setItem(CLAVE_TOKEN, valor); } catch { /* sin almacenamiento: tocará volver a entrar */ }
  },
  borrar() {
    try { localStorage.removeItem(CLAVE_TOKEN); } catch { /* nada que borrar */ }
  },
};

export class ErrorApi extends Error {
  constructor(mensaje, status) {
    super(mensaje);
    this.status = status; // 0 = no hay conexión
  }
}

// La sesión (sesion.jsx) se apunta aquí para enterarse si el servidor dice que el token ya no vale
let alCaducarSesion = () => {};
export function avisarCuandoCaduqueLaSesion(funcion) {
  alCaducarSesion = funcion;
}

export async function peticion(ruta, { metodo = "GET", datos, formulario, timeout = 15000 } = {}) {
  const cabeceras = {};
  const t = token.leer();
  if (t) cabeceras.Authorization = `Bearer ${t}`;

  let cuerpo;
  if (formulario) {
    cuerpo = formulario; // FormData (subir imágenes): el navegador pone su propia cabecera
  } else if (datos !== undefined) {
    cabeceras["Content-Type"] = "application/json";
    cuerpo = JSON.stringify(datos);
  }

  // Si el servidor no contesta en `timeout` ms, cortamos (si no, la app se quedaría colgada)
  const control = new AbortController();
  const temporizador = setTimeout(() => control.abort(), timeout);
  let respuesta;
  try {
    respuesta = await fetch(API_URL + ruta, { method: metodo, headers: cabeceras, body: cuerpo, signal: control.signal });
  } catch {
    throw new ErrorApi("No hay conexión con el servidor. Comprueba tu internet y vuelve a probar.", 0);
  } finally {
    clearTimeout(temporizador);
  }

  if (respuesta.status === 204) return null;
  let json = null;
  try { json = await respuesta.json(); } catch { /* respuesta sin JSON */ }

  if (!respuesta.ok) {
    if (respuesta.status === 401 && t) alCaducarSesion();
    throw new ErrorApi(json?.error || `Error inesperado (${respuesta.status})`, respuesta.status);
  }
  return json;
}

export const api = {
  get: (ruta, opciones) => peticion(ruta, opciones),
  post: (ruta, datos = {}) => peticion(ruta, { metodo: "POST", datos }),
  put: (ruta, datos = {}) => peticion(ruta, { metodo: "PUT", datos }),
  borrar: (ruta, datos) => peticion(ruta, { metodo: "DELETE", datos }),
  subir: (ruta, formulario) => peticion(ruta, { metodo: "POST", formulario, timeout: 30000 }),
};
