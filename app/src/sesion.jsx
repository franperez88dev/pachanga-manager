/*
 * CONTEXTO DE REACT: un "contexto" es una forma de compartir datos con TODOS los
 * componentes de la app sin pasarlos de padre a hijo por props. Aquí guardamos
 * quién ha iniciado sesión; cualquier pantalla puede leerlo con useSesion().
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { api, avisarCuandoCaduqueLaSesion, token } from "./api";

const SesionContext = createContext(null);

export function SesionProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  // "comprobando": al abrir la app, preguntamos al backend si el token guardado sigue valiendo
  const [comprobando, setComprobando] = useState(() => Boolean(token.leer()));
  const [errorInicial, setErrorInicial] = useState(null);

  // Al entrar o salir siempre se empieza desde Inicio (no en la última pantalla que se vio).
  // useNavigate funciona aquí porque SesionProvider está dentro de <HashRouter> (main.jsx).
  const navegar = useNavigate();

  const salir = useCallback(() => {
    token.borrar();
    navegar("/", { replace: true });
    setUsuario(null);
  }, [navegar]);

  const recargarUsuario = useCallback(async () => {
    const datos = await api.get("/api/yo");
    setUsuario(datos.usuario);
    return datos.usuario;
  }, []);

  /*
   * EFECTO (useEffect): código que se ejecuta DESPUÉS de pintar el componente, para
   * cosas "de fuera" de React: llamadas al servidor, temporizadores... El array del
   * final ([] aquí) dice cuándo repetirlo; vacío = solo una vez, al aparecer.
   */
  useEffect(() => {
    avisarCuandoCaduqueLaSesion(salir);
  }, [salir]);

  useEffect(() => {
    if (!comprobando) return;
    recargarUsuario()
      .catch((e) => {
        // 401: el token ya no vale (api.js ya ha cerrado la sesión). Otro error: sin conexión.
        if (e.status !== 401) setErrorInicial(e.message);
      })
      .finally(() => setComprobando(false));
  }, [comprobando, recargarUsuario]);

  const entrar = useCallback((nuevoToken, nuevoUsuario) => {
    token.guardar(nuevoToken);
    navegar("/", { replace: true });
    setUsuario(nuevoUsuario);
  }, [navegar]);

  const reintentar = useCallback(() => {
    setErrorInicial(null);
    setComprobando(true);
  }, []);

  // useMemo: solo crea un objeto nuevo si cambia algo; así no se repintan de más los que lo usan
  const valor = useMemo(
    () => ({ usuario, comprobando, errorInicial, entrar, salir, recargarUsuario, setUsuario, reintentar }),
    [usuario, comprobando, errorInicial, entrar, salir, recargarUsuario, reintentar],
  );
  return <SesionContext.Provider value={valor}>{children}</SesionContext.Provider>;
}

export function useSesion() {
  return useContext(SesionContext);
}
