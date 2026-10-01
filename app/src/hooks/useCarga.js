/*
 * HOOK PROPIO: una función que empieza por "use" y usa otros hooks. Sirve para no
 * repetir en cada pantalla la misma lógica de "cargando / error / datos".
 *
 *   const { datos, cargando, error, recargar, poner } = useCarga("/api/jugadores");
 */
import { useCallback, useEffect, useState } from "react";
import { api } from "../api";

export function useCarga(ruta) {
  const [estado, setEstado] = useState({ datos: null, cargando: Boolean(ruta), error: null });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    if (!ruta) return;
    // Si el componente desaparece o cambia la ruta antes de que llegue la respuesta, la ignoramos
    let vigente = true;
    setEstado((e) => ({ ...e, cargando: true, error: null }));
    api.get(ruta)
      .then((datos) => vigente && setEstado({ datos, cargando: false, error: null }))
      .catch((e) => vigente && setEstado((anterior) => ({ ...anterior, cargando: false, error: e.message })));
    return () => { vigente = false; };
  }, [ruta, version]);

  const recargar = useCallback(() => setVersion((v) => v + 1), []);
  // Para actualizar los datos con lo que devuelve una acción (p. ej. votar) sin volver a pedirlos
  const poner = useCallback((datos) => setEstado({ datos, cargando: false, error: null }), []);
  return { ...estado, recargar, poner };
}
