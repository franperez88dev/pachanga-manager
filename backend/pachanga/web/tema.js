// Tema claro u oscuro. Este archivo se carga en el <head>, antes que la app, para que la
// página ya salga con el color correcto (si lo hiciera React, se vería un fogonazo del otro tema).
// Si el usuario no ha elegido nada, no se pone nada y manda el tema del móvil (ver estilos.css).
// El botón que lo cambia está en src/tema.js.
(function () {
  try {
    var elegido = localStorage.getItem("pachanga.tema");
    if (elegido === "claro" || elegido === "oscuro") {
      document.documentElement.setAttribute("data-tema", elegido);
    }
  } catch (e) { /* sin almacenamiento (modo privado...): se queda el tema del móvil */ }
})();
