# Decisiones y cambios respecto a PROMPT.md

Cuando esto y `PROMPT.md` se contradigan, **manda este archivo** (son cambios acordados después).

## ⭐ Cambio de rumbo (03/10/2026): aplicación web en PythonAnywhere, sin APK

Sustituye a todo lo que `PROMPT.md` dice sobre APK, Capacitor, firma, hosting y Google Play
(secciones 2.1 y 9, y fases 3, 4 y 6), y al apartado "Fase 3: APK" de más abajo.

- **Solo web.** La app se abre en el navegador del móvil (Android o iPhone) y se puede "Añadir a
  pantalla de inicio" (manifiesto web + iconos). **No hay APK ni publicación en Google Play.**
- **Hosting: PythonAnywhere, plan gratuito**, en `https://TU_USUARIO.pythonanywhere.com`.
  Verificado el 03/10/2026: 1 web, 512 MB, 100 s de CPU al día, sin MySQL en cuentas nuevas y
  **hay que renovar la web cada mes** con un botón.
- **Un solo servidor para todo.** Flask entrega la web compilada (`backend/pachanga/web`) y la API
  (`/api/...`) desde el mismo dominio: la app llama con rutas relativas y **no hace falta CORS**
  en producción (solo en el PC, para Vite).
- **La web se compila en el PC** (`npm run build` en `app/`) y la carpeta compilada **se sube a git**.
  En PythonAnywhere no hay Node: se publica con `git pull` + **Reload**.
- **Base de datos: SQLite** también en producción (`backend/instance/pachanga.db`). En PythonAnywhere
  el disco no se borra. Copia de seguridad = descargar ese archivo.
- **Repositorio público** en GitHub (`franperez88dev/pachanga-manager`) para poder clonarlo en
  PythonAnywhere sin credenciales. No contiene secretos.
- **`CONFIAR_EN_PROXY=1` en el servidor** (obligatorio): PythonAnywhere va detrás de un proxy y, sin
  esto, el bloqueo de login por IP afectaría a todos a la vez.
- **Comandos de prueba** (`flask datos-demo`, `flask demo-votar`): ya no se protegen con "solo SQLite"
  (producción también lo es) sino con `PERMITIR_DATOS_DEMO=1`, que solo se pone en el PC.
- **Dependencias**: fuera `psycopg` (PostgreSQL) y `gunicorn`. PythonAnywhere usa su propio servidor
  WSGI e importa `backend/wsgi.py` (variable `application`), que carga el `.env`.
- **Seguridad de la web**: `index.html` sin caché y con Content-Security-Policy (solo recursos del
  propio servidor); archivos de `/assets/` con caché larga; `X-Content-Type-Options: nosniff`.
- **Versión** de `app/package.json` visible en Perfil, para comprobar qué versión ve cada móvil.
- **Todo lo del APK se ha retirado del proyecto** (Capacitor, `app/android`, scripts, firma). Está
  intacto en la etiqueta de git **`con-apk-android`** por si algún día se retoma. El keystore sigue
  en `C:\Users\SuFran\.pachanga\` (fuera del repositorio).
- Los pasos para publicar están en el README, apartado 6.

## Fase 0 (30/09/2026)
- La decisión de hosting se aplaza a la Fase 4 (las condiciones de los planes gratuitos cambian a menudo).
- `applicationId` definitivo: `com.pachanga.manager`.
- Google Play exige `targetSdk 36` desde el 31/08/2026; Capacitor 8 ya usa 36.

## Acceso: mote + PIN (sustituye al "dorsal como clave" de la sección 3)
- Al registrarse, la app genera un **PIN aleatorio de 4 cifras** y lo enseña **una sola vez**. Se entra con **mote + PIN**.
- El PIN se guarda cifrado (hash scrypt); nadie puede consultarlo, ni el admin.
- Si alguien olvida el PIN, un admin le **genera uno nuevo** desde el panel (se lo pasa por WhatsApp) y sus sesiones abiertas se cierran.
- Se mantiene el bloqueo de intentos (5 por mote / 10 por IP, 15 minutos) y el mensaje de error idéntico.
- El **dorsal es público** (número de camiseta) y **se reutiliza**: a cada alta nueva le toca el dorsal libre más bajo (p. ej. el de una cuenta borrada).
- Un alta **rechazada se borra**, y su mote y su dorsal quedan libres.

## Goles, gpp y asistencias (sustituye a la sección 4.3)
1. El admin **cierra el partido indicando el resultado** (goles del Blanco y del Negro). Se puede corregir después.
2. Solo con el partido cerrado se apuntan goles. Dos caminos:
   - **Planilla del admin**: en ese momento, primero los goles y los **gpp** (goles en propia puerta) de cada jugador con + y −, botón Confirmar, y después las asistencias igual. Queda todo confirmado. La planilla es la versión definitiva y sustituye a lo apuntado antes (la app la precarga con lo que los jugadores tengan pendiente).
   - **"Sig."**: el admin se lo salta y cada convocado apunta lo suyo desde la app; queda pendiente hasta que el admin lo confirma o descarta. El jugador puede anular su pendiente (botón rojo de doble confirmación).
3. Un **gpp** suma un gol al equipo rival, no cuenta como gol propio y tiene **columna propia** en la clasificación y en el perfil.
4. Si los goles no cuadran con el resultado (o hay más asistencias que goles), la app **avisa pero deja guardar**.

## Asistencias ocultas (01/10/2026)
- **De momento solo se llevan goles (y gpp).** La app no muestra ni pide asistencias.
- El backend las conserva como campo opcional (vale 0 si no llega) para poder reactivarlas sin migrar datos.

## Avatares (01/10/2026)
- Cada jugador elige su avatar al registrarse y puede cambiarlo cuando quiera desde su perfil.
- **Personalizable**: color de piel, peinado + color (calvo, corto, tupé, rizos, melena o cresta), barba + color (sin barba, bigote, perilla o completa; la "de 3 días" se quitó porque quedaba mal).
- **Botón "Aleatorio"**, que se puede pulsar las veces que quiera; a veces sale un dibujo especial (alien, perro, gato, pepino, calabaza).
- Si no elige nada, le toca uno al azar.
- **Los avatares disponibles son solo los incluidos en la app** (el muñeco personalizable y los 5 especiales). La opción de que el admin subiera avatares nuevos se quitó el 01/10/2026 a petición de Fran.

## Equipos
- Se muestran las fuerzas totales con números ("15,0 vs 14,5"). Se sabe que, rebarajando muchas veces, podrían deducirse medias aproximadas; se acepta a cambio del pique entre amigos.
- Tolerancia de "Rebarajar": 0,5 puntos sobre el mejor reparto posible (explicado en `backend/pachanga/equipos.py`).
- **Vista de equipos sobre una pista de fútbol sala en horizontal** (fondo azul `#002db3`; Nevados a la izquierda y Sombras a la derecha), en formación **portero – 2 defensas – 2 delanteros**. Los defensas van al borde de su área y los delanteros, cerca del círculo central en su propio campo. Cada jugador se ve con su avatar redondo, su dorsal y su mote debajo.
- Quién juega de portero, defensa o delantero se sortea al hacer los equipos y se guarda, para que todos vean la misma alineación.
- **Orden en portería**: al hacer los equipos se sortea en cada equipo el orden de los 5 en la portería. Empieza el que sale de portero en la pista. Se muestra solo la lista numerada (sin minutos ni explicaciones), con la columna de Sombras F.C. en fondo negro.

## Votación para rebarajar (01/10/2026; sustituye al "Rebarajar" libre)
- El admin hace los equipos **una sola vez**.
- Después, a cada convocado le aparece **"¿Deseas una nueva selección de equipo?" Sí / No**. **Se vota una sola vez y no se puede cambiar**; tras un nuevo reparto se vuelve a votar. Solo se ven los totales; cada uno ve únicamente su propio voto.
- Con **6 síes o más** (6 contra 4 ya es mayoría) el admin puede rebarajar. El nuevo reparto sigue sin repetir el anterior.
- **Máximo 3 repartos** en total (el inicial + 2 cambios). Cada reparto abre una votación nueva desde cero.
- "Volver a elegir" solo sirve para **cambiar convocados**: con los mismos 10, los equipos se mantienen; si cambia alguien, se rehacen los equipos y la cuenta de repartos y votos empieza de cero.
- Umbral y máximo configurables (`VOTOS_PARA_REBARAJAR`, `MAX_REPARTOS`).

## Fase 2: frontend (01/10/2026)
- Router: paquete **`react-router` 8** con `HashRouter`. `react-router-dom` (el que nombraba el PROMPT) ya no se publica en la versión 8; es el mismo código, solo cambia el nombre del `import`.
- Fuentes Barlow / Barlow Condensed empaquetadas con `@fontsource` (sin CDN).
- `app/.env.development` (y más adelante `.env.production`) **sí van a git**: la URL del backend no es secreta.
- Asistencias: interruptor `MOSTRAR_ASISTENCIAS` en `app/src/config.js` (ahora `false`).
- Navegación inferior: Inicio · Partidos · Tabla · Valorar · (Admin) · Perfil.
- Comandos solo para pruebas en local: `flask datos-demo` y `flask demo-votar` (desde el 03/10/2026 exigen `PERMITIR_DATOS_DEMO=1`).

## Fase 3: APK (02/10/2026) — RETIRADO el 03/10/2026 (ver "Cambio de rumbo" arriba)
- **Capacitor 8.5** con `appId` `com.pachanga.manager`. El proyecto Android está en `app/android` y sí va a git (menos lo generado).
- **JDK 21** para compilar: Gradle 8.14.3 (el que trae Capacitor 8) solo funciona hasta Java 24, y el JBR de Android Studio es Java 25. Se descarga desde Android Studio (*Gradle JDK → Download JDK*).
- **targetSdk / compileSdk 36** (Android 16), que es lo que exige Google Play desde el 31/08/2026; minSdk 24.
- **Móvil contra el backend local por USB** con `adb reverse tcp:5000 tcp:5000` y la URL `http://127.0.0.1:5000` (`app/.env.movil`, `npm run build:movil`).
- **HTTP sin cifrar solo en la versión de pruebas** y solo hacia `localhost`/`127.0.0.1` (`app/android/app/src/debug/`). La versión release no lo permite: solo HTTPS.
- No se ha configurado la alternativa por WiFi (IP del PC): necesitaría permitir HTTP hacia una IP de la red y "contenido mixto".
- **Firma**: un único keystore en `C:\Users\SuFran\.pachanga\pachanga.jks` (fuera del repo), con la contraseña en `app/android/keystore.properties` (no va a git). Lo usan tanto la versión debug como la release. Alternativa para GitHub Actions: variables `PACHANGA_KEYSTORE_*`.
- **Versión** en un solo sitio (`app/package.json`). `versionCode = mayor·10000 + menor·100 + parche`. Se sube con `npm run version:subir`.
- **Icono adaptativo** (balón blanco sobre verde, con versión monocromo para los iconos temáticos) y pantalla de arranque verde con el balón. El mismo diseño está en `recursos-play/icono-512.png` y en el favicon.
- **Botón "atrás"** de Android: vuelve a la pantalla anterior; en Inicio cierra la app.
- **Márgenes de pantalla** con las variables `--safe-area-inset-*` que inyecta Capacitor 8, para que nada quede bajo la barra de estado.
- Permisos de Android: solo `INTERNET`.

## Pendiente de decidir más adelante
- Migraciones de base de datos (Flask-Migrate): hacen falta antes de publicar cualquier cambio que modifique las tablas, para no perder los datos de producción.
