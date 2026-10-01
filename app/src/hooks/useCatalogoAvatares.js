// El catálogo de avatares se pide una vez y se reutiliza en todas las pantallas
import { useEffect, useState } from "react";
import { api } from "../api";

let promesa = null;

export function olvidarCatalogo() {
  promesa = null; // tras subir o retirar un avatar, para que se vuelva a pedir
}

export function useCatalogoAvatares() {
  const [catalogo, setCatalogo] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let vigente = true;
    promesa ??= api.get("/api/avatares").catch((e) => { promesa = null; throw e; });
    promesa.then((c) => vigente && setCatalogo(c)).catch((e) => vigente && setError(e.message));
    return () => { vigente = false; };
  }, []);

  return { catalogo, error };
}
