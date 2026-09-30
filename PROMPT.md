# Prompt para Claude Code: Pachanga Manager (app Android en APK) — v3

> Cómo usarlo: dentro de la carpeta `pachanga-manager`, junto a este archivo (`PROMPT.md`), crea la subcarpeta `referencia/` y mete ahí `prototipo.html` y una subcarpeta `escudos/` con las dos imágenes. Abre una terminal EN `pachanga-manager`, ejecuta `claude` y escribe: "Lee PROMPT.md entero y sigue sus instrucciones, empezando por la Fase 0".

---

## 1. Quién soy y qué quiero

Soy Fran, desarrollador autodidacta (Python, Flask y SQLAlchemy los manejo bien; estoy aprendiendo JavaScript y React: conozco lo básico de componentes, props y estado, pero me falta soltura). Vivo en España, así que la app y tus explicaciones van en **español**.

Quiero una **app Android** llamada **Pachanga Manager** para organizar los partidos de fútbol de mi peña de amigos.

**Plan por etapas (importante, respétalo):**
1. **Etapa local (Fases 0-3)**: todo funciona en mi ordenador y lo pruebo yo en **mi móvil real**, con el backend corriendo en mi PC. Sin hosting, sin pagos y sin subir nada a ningún sitio.
2. **Etapa de reparto (Fase 4, solo cuando yo lo apruebe)**: despliegue del backend y APK firmado para pasárselo a los colegas por WhatsApp/Drive.
3. **Etapa Google Play (Fase 6, solo cuando yo lo apruebe)**: publicar en mi cuenta de desarrollador de Google Play que ya tengo (no sé si sigue activa; ver Fase 6).

Aunque la publicación en Play sea opcional y posterior, **construye desde el principio de forma que no haya que rehacer nada para llegar a ella** (nombre de paquete definitivo, versionado, iconos, HTTPS en producción, etc.; detalle en las secciones 9 y 10).

Es una app **compartida**: todos los colegas ven los mismos datos (jugadores, partidos, goles, clasificación), así que en producción necesita un **backend real en internet** además de la app, y ese backend debe estar disponible siempre que un colega abra la app (ver 2.1). En la etapa local, el backend corre en mi PC.

## 2. Arquitectura (decidida, no la cambies sin preguntarme)

- **Backend**: Flask + Flask-SQLAlchemy, API REST que devuelve JSON. Base de datos por variable de entorno `DATABASE_URL`: SQLite en local y **PostgreSQL externo** en producción (nunca SQLite en el hosting: el disco se borra en cada reinicio). Autenticación por token (JWT o token firmado con `itsdangerous`) en la cabecera `Authorization: Bearer ...`. Servidor de producción: gunicorn.
- **Frontend**: **React + Vite**, mobile-first. Componentes de función y hooks (`useState`, `useEffect`, y un contexto para la sesión). Para navegar, `react-router-dom` con `HashRouter` (funciona bien dentro de Capacitor). Sin librerías pesadas de UI ni de estado: quiero entender lo que hay. Elijo React porque es lo que quiero aprender para trabajar de frontend. **Cada vez que introduzcas un concepto de React nuevo (efectos, contexto, rutas, formularios controlados), explícalo en 2-3 frases** y comenta el código en español donde no sea evidente.
- **Empaquetado**: **Capacitor** envolviendo el build de Vite (`dist/`) como app Android nativa. `appId`: `com.pachanga.manager`.
- **CORS**: la app Capacitor hace peticiones desde el origen `https://localhost`. Configura CORS para permitirlo (y `http://localhost:*` / `http://127.0.0.1:*` en desarrollo).
- **URL del backend** en una única variable de entorno de Vite (`VITE_API_URL`), para cambiarla entre local y producción sin tocar código.
- Comunicaciones por HTTPS en producción. Si el backend usa HTTP en local, configura Capacitor/Android solo para desarrollo.

Estructura de carpetas (monorepo):

```
pachanga-manager/
  PROMPT.md
  referencia/     prototipo.html + escudos/ (solo referencia, no se publica)
  backend/        Flask: app, modelos, rutas, tests, requirements.txt
  app/            React + Vite + Capacitor (src/, android/)
  render.yaml     Despliegue del backend (o el equivalente del hosting elegido)
  README.md       Cómo arrancar, compilar el APK y actualizar la app
```

### 2.1 Backend siempre disponible (requisito de la Fase 4, NO lo hagas antes de mi OK)

Durante las Fases 0-3 el backend corre en local y no se decide ni se contrata nada. Cuando llegue la Fase 4: los planes gratuitos "duermen" el servidor tras ~15 minutos sin tráfico y el primer arranque tarda hasta un minuto. Además, en Render la **base de datos PostgreSQL gratuita caduca a los 30 días** (y se borra 14 días después), así que **no uses el Postgres gratuito de Render**. Verifica las condiciones actuales antes de decidir y preséntame estas opciones con tu recomendación:

- **Opción A (gratis)**: web service gratuito + PostgreSQL gratuito de un proveedor sin caducidad de 30 días (por ejemplo Neon o Supabase; comprueba límites y pausas por inactividad) + un **ping periódico al endpoint `/health`** cada ~10 minutos con un servicio gratuito tipo UptimeRobot para que no se duerma. Aviso: mantener despierto un plan gratuito con pings no es un método soportado oficialmente, puede fallar o cambiar.
- **Opción B (de pago, fiable)**: web service de pago barato (sin spin-down) + base de datos externa. Indícame el coste real actual.
- En cualquier caso, el frontend debe mostrar una pantalla **"Conectando con el servidor…"** con reintentos automáticos si el backend tarda en responder, y mensajes de error claros si no hay conexión.
- Crea un endpoint `GET /health` ligero (sin tocar la base de datos, o tocándola mínimamente).

## 3. Roles y acceso (login con dorsal)

- **La clave de acceso es el dorsal.** Al registrarse, a cada jugador se le asigna un **dorsal numérico correlativo** (01 = yo, el admin; luego 02, 03…). Los dorsales **nunca se reutilizan**, aunque el alta se rechace.
- Se entra con **mote + dorsal**. El mote es único (sin distinguir mayúsculas).
- Al terminar el registro se muestra **una vez** una pantalla grande con su dorsal ("Tu dorsal es el 07. Es tu clave para entrar, no se la digas a nadie").
- **El dorsal no se muestra nunca a otros usuarios** (ni en la cuadrícula de convocatoria, ni en clasificación, ni en perfiles, ni en las respuestas de la API que ven los jugadores), porque quien lo vea podría entrar como ese colega. Solo un admin puede consultarlo, únicamente en el panel de admin, por si alguien lo olvida (me lo pregunta por WhatsApp).
- Roles: **admin** y **jugador**. La app sabe cuál eres al iniciar sesión y muestra u oculta pantallas y botones según el rol. **Los permisos se validan SIEMPRE en el backend**, no solo ocultando botones.
- **Registro**: mote (el nombre por el que le llamamos en la pachanga) y nombre real opcional. Queda **pendiente** y solo ve "Esperando aprobación del admin". No puede usar nada hasta que un admin lo apruebe.
- **Primer admin (yo)**: créalo con un comando CLI de Flask (`flask create-admin`), con dorsal 01, sin datos escritos en el código ni subidos a git.
- El admin puede **aprobar o rechazar** altas y **promocionar/degradar** a otros admins (siempre debe quedar al menos uno).
- **Seguridad del dorsal** (es una clave de pocos dígitos, así que hay que compensarlo): bloqueo temporal tras varios intentos fallidos por mote y por IP (por ejemplo 5 intentos y 15 minutos de espera; constantes configurables), respuestas de error idénticas para "mote inexistente" y "dorsal incorrecto", y token de sesión con caducidad larga para que no tengan que teclearlo cada vez (guardado en el almacenamiento de la app). Si te parece insuficiente, díselo al final de la Fase 1 y propón alternativas (por ejemplo un PIN independiente del dorsal), pero **implementa lo que aquí se pide**.

## 4. Funcionalidades

### 4.1 Partidos (solo admin)
- Crear un partido (fecha, hora, lugar).
- **Convocatoria**: elegir **exactamente 10 jugadores** entre los aprobados. Vista en **cuadrícula de dos columnas** con **buscador en vivo** por mote y marcado tipo checkbox. No se puede continuar si no son 10.
- **Crear equipos** (botón dentro de la misma pestaña de Convocatoria): desaparece la cuadrícula y aparecen los dos equipos en su lugar. Botones **"Volver a elegir"** y **"Rebarajar"**.
- **Cerrar partido** cuando termina: a partir de ahí cuenta como partido jugado para los convocados.

### 4.2 Equipos equilibrados
- Dos equipos de 5: **Blanco** y **Negro**.
  - Blanco = **"Nevados C.F."** (escudo con oso polar).
  - Negro = **"Sombras F.C."** (escudo con lobo).
  - Los escudos están en `referencia/escudos/`. Úsalos en la vista de equipos; si faltan, pon un marcador de color provisional.
- Algoritmo: cada jugador tiene una **media de valoraciones** (ver 4.4). Repartir los 10 en 2 equipos de 5 con la **suma de medias lo más parecida posible**. Son solo 252 combinaciones: **prueba todas por fuerza bruta**.
- **Rebarajar**: elige al azar entre los repartos con diferencia de fuerza dentro de una tolerancia pequeña (constante configurable que razones y dejes documentada) y **nunca repitas el reparto anterior**.
- Jugador sin valoraciones todavía: usa como media provisional la media global de todos los jugadores.
- Muestra la **fuerza total de cada equipo** (ej.: 15,0 vs 14,5) y la diferencia. **Nunca la media individual de nadie** (ver 4.4).
- Guarda los equipos en base de datos para que todos los colegas los vean en su app.

### 4.3 Goles y asistencias
- Cada jugador convocado **reporta desde su cuenta** sus goles y asistencias de un partido.
- El reporte queda **pendiente**; el **admin lo confirma o lo descarta**. Solo los confirmados cuentan en la clasificación.
- El jugador puede **anular un reporte pendiente propio** con un **botón rojo de doble confirmación** (primer toque: "¿Seguro?"; segundo toque: anula). El admin puede descartar cualquier reporte.

### 4.4 Valoración secreta de calidad
- Cada usuario ve a sus compañeros, pulsa sobre uno y le da de **1 a 5 estrellas** a su "calidad de jugador". Se envía **una sola vez y queda bloqueado**. Nadie puede valorarse a sí mismo.
- Restricción en base de datos: **UNIQUE(valorador, valorado)**.
- **Privacidad**: las valoraciones individuales y la media de cada jugador **no se muestran a nadie** (tampoco al admin) y **la API no las devuelve a ningún usuario**. Solo se ve la **fuerza total de cada equipo**. Un usuario sí ve que ya valoró a alguien ("Valorado ✓").
- La media se calcula solo en el backend al crear equipos.

### 4.5 Clasificación
- Tabla con **goles, asistencias y partidos jugados** por jugador, **ordenable por cualquiera de las tres columnas**. Solo cuentan datos confirmados y partidos cerrados.

### 4.6 Perfil de jugador
- Ficha simple: mote, goles, asistencias, partidos jugados. Sin dorsal ni datos de acceso visibles para otros.

## 5. Modelo de datos (orientativo, ajústalo con criterio)

- `User`: id, mote (único), nombre_real, **dorsal (entero único, autoincremental, nunca reutilizado)**, rol (`admin`/`jugador`), estado (`pendiente`/`aprobado`/`rechazado`), fecha_alta, intentos_fallidos, bloqueado_hasta.
- `Match`: id, fecha, lugar, estado (`abierto`/`cerrado`), equipos_generados (bool).
- `MatchPlayer`: match_id, user_id, equipo (`blanco`/`negro`/null).
- `Rating`: rater_id, rated_id, stars (1-5), fecha, **UNIQUE(rater_id, rated_id)**.
- `StatReport`: id, match_id, user_id, goles, asistencias, estado (`pendiente`/`confirmado`/`descartado`/`anulado`).

## 6. Pantallas

Inicio de sesión (mote + dorsal) / registro / dorsal asignado / espera de aprobación · Inicio (próximo partido y su estado) · Convocatoria y equipos (admin) · Mis goles y asistencias · Valorar compañeros (lista y detalle con estrellas) · Clasificación · Perfil · Panel de admin (altas pendientes, gestión de admins, goles por confirmar, consulta de dorsal de un colega que lo olvidó) · Pantalla "Conectando con el servidor…".

## 7. Diseño

- **Mobile-first**, pensado para usarse con una mano. Botones grandes. Gestiona el botón "atrás" de Android.
- Estética de campo de fútbol: verde como color principal, tarjetas limpias, tipografía deportiva (Barlow / Barlow Condensed). **Empaqueta las fuentes en local** (no las cargues de un CDN).
- **Modo oscuro** automático según el sistema.
- `referencia/prototipo.html` es el prototipo clicable que ya diseñamos (datos de demo en memoria, sin backend). Úsalo como **referencia visual y de flujo** (colores, tarjetas, pestañas, cuadrícula de convocatoria, equipos, estrellas, botón de doble confirmación), **no lo copies a ciegas**: reescríbelo como componentes React. Abre el archivo y estúdialo antes de la Fase 2. Ojo: el prototipo puede mostrar el dorsal en algunas vistas; en la app real debe seguirse la regla de la sección 3.
- Estados vacíos, de carga y de error claros en todas las pantallas.
- Icono de app y pantalla de arranque sencillos con el tema de la peña.

## 8. Seguridad (mínimos obligatorios)

- Token con caducidad razonable. Sin datos sensibles en logs.
- `.env` y claves **fuera de git** (`.gitignore` desde el primer commit). Ejemplo en `.env.example`.
- Rate limiting y bloqueo de login (ver sección 3).
- Validación de entrada en el backend y códigos HTTP correctos (401, 403, 404, 409, 429...).
- Comprueba permisos por rol y por propietario en cada endpoint (un jugador no puede confirmar goles, ver valoraciones ajenas, ver dorsales ni tocar datos de otro).

## 9. Entorno y cómo generar el APK

Trabajo en **VS Code + GitHub Desktop** (estoy aprendiendo git y GitHub). Para compilar el APK hace falta **Node.js, JDK 17 y el Android SDK** (o Android Studio).

- **Fase 0**: comprueba qué tengo instalado (`node -v`, `java -version`, `ANDROID_HOME`, etc.) y dime qué falta **antes de instalar nada**. No instales cosas grandes sin preguntarme.
- Para compilar: en `app/`, `npm run build`, luego `npx cap sync android`, y **dentro de `app/android`**, `./gradlew assembleDebug` (en Windows, `gradlew.bat assembleDebug`). El APK sale en `app/android/app/build/outputs/apk/debug/app-debug.apk`.
- **Firma del APK**: todos los APK que reparta deben ir firmados con **la misma clave**, o Android no dejará actualizar encima de la versión instalada. Genera **un solo keystore** propio, configúralo en Gradle leyendo contraseñas de variables de entorno o de un archivo **no versionado**, y úsalo siempre, también en GitHub Actions si lo montamos (guardando el keystore como secreto). Explícame en la Fase 3, con palabras sencillas, qué es la firma y por qué el keystore hay que **guardarlo a buen recaudo** (copia en un sitio seguro fuera del repositorio).
- **Plan B si mi PC no puede compilar**: workflow de **GitHub Actions** que compile el APK y lo deje descargable.
- Recuérdame que los colegas deben permitir "instalar apps de orígenes desconocidos" para instalar el APK.

### 9.1 Probar en mi móvil contra el backend local (Fase 3)

Quiero probar la app en mi móvil real mientras el backend corre en mi PC. Propón y configura el método más sencillo y explícamelo paso a paso (terminal, carpeta y qué hace cada comando). Opciones a valorar:
- **Por USB con `adb reverse tcp:5000 tcp:5000`**: el móvil accede al backend de mi PC como si fuera `localhost`. Requiere activar "Opciones de desarrollador" y "Depuración por USB" en el móvil. Es mi preferida si funciona bien.
- **Por WiFi con la IP de mi PC** (por ejemplo `http://192.168.x.x:5000`): Android bloquea HTTP sin cifrar por defecto, así que habría que permitirlo **solo en la build de desarrollo** y nunca en la de producción. Recuérdame abrir el puerto en el firewall si hace falta.
- En ambos casos, el backend debe escuchar en `0.0.0.0` solo cuando yo lo pida, y la URL de la API sale de `VITE_API_URL`.

### 9.2 Preparado para Google Play desde el principio

No publiques nada, pero deja resuelto lo que luego costaría rehacer:
- **`applicationId` definitivo `com.pachanga.manager`** (no se puede cambiar una vez publicada la app). Confírmamelo en la Fase 0.
- `versionCode` (entero que sube en cada versión) y `versionName` gestionados en un solo sitio, y un script o comando documentado para subirlos.
- Nivel de API objetivo (`targetSdkVersion`) al que **Google Play exija en ese momento**: verifícalo en la documentación oficial vigente, no de memoria.
- **Icono adaptativo** de Android y pantalla de arranque con el tema de la peña. Icono de tienda de 512x512 y una imagen de cabecera si son necesarios (déjame la lista de recursos gráficos que pide Play).
- Producción **solo por HTTPS**, sin tráfico HTTP sin cifrar en la build de release.
- Permisos de Android **mínimos** (solo Internet). No pidas nada más.
- La app tiene registro de usuarios, así que Play exigirá una **vía para que un usuario pida borrar su cuenta y sus datos** (dentro de la app y con una URL web). Diséñalo: endpoint de borrado de cuenta y pantalla en Perfil (con doble confirmación). Verifica el requisito vigente.
- Prepara borradores (sin publicarlos) de: **política de privacidad** (qué datos se guardan: mote, nombre real opcional, dorsal, valoraciones, goles), textos de la ficha de la tienda en español y una lista de las **capturas de pantalla** que habrá que sacar.
- Para Play hace falta un paquete **`.aab`** (`./gradlew bundleRelease` dentro de `app/android`) en vez de APK. Deja el comando y la configuración de firma de subida documentados, aunque no lo ejecutes hasta la Fase 6.

## 10. Cómo quiero que trabajes

1. **Por fases, con parada al final de cada una** para que yo lo pruebe y te dé el OK:
   - Fase 0: comprobar el entorno y confirmar el plan, incluida la decisión de hosting (sección 2.1).
   - Fase 1: backend completo (modelos, auth con dorsal, roles, bloqueo de intentos, endpoints) con **tests `pytest`** del algoritmo de equipos, de los permisos y de la privacidad de valoraciones y dorsales.
   - Fase 2: frontend React funcionando en el navegador contra el backend local.
   - Fase 3: empaquetar con Capacitor, generar el APK firmado de depuración e **instalarlo en mi móvil contra el backend local** (sección 9.1). Aquí termina la etapa local y **te detienes hasta que yo diga que me gusta**.
   - Fase 4 (**solo con mi OK explícito**): decidir hosting (sección 2.1), desplegar el backend y la base de datos, apuntar la app a la URL pública y generar el APK firmado final para los colegas.
   - Fase 5: `README.md` con cómo arrancar en local, compilar, actualizar el backend y repartir nuevas versiones del APK. Puede hacerse ya al acabar la Fase 3 y completarse después.
   - Fase 6 (**solo con mi OK explícito, cuando yo me vea capacitado**): publicar en Google Play. Antes de tocar nada, guíame para **comprobar el estado de mi cuenta de desarrollador** (en la Play Console: si sigue activa, si me pide verificar datos de contacto, si mi antiguo juego del tres en raya sigue publicado y si hay correos de cierre por inactividad) y **verifica en la documentación oficial vigente** los requisitos para mi tipo de cuenta (por ejemplo, si me exigen prueba cerrada con testers antes de producción, según cuándo se creó mi cuenta). Después, paso a paso: crear la ficha, subir el `.aab` primero a **prueba interna**, rellenar los formularios (seguridad de datos, clasificación de contenido, política de privacidad, borrado de cuenta) y solo entonces, si procede, prueba cerrada y producción. Yo pulso siempre el botón final de enviar.
2. **Yo estoy aprendiendo**: cada vez que me pidas ejecutar un comando, dime **en qué terminal y en qué carpeta** ejecutarlo y **qué hace cada paso**. Explica las decisiones importantes en pocas frases.
3. Haz **commits pequeños y con mensaje claro** (los revisaré en GitHub Desktop). No hagas push ni despliegues sin preguntarme.
4. Si una decisión cambia de verdad lo que construyo (hosting, librería, seguridad), **pregúntame antes** con opciones concretas y tu recomendación.
5. Si algo de este documento se contradice o no es viable, dímelo en vez de improvisar en silencio.

## 11. Criterios de aceptación

- [ ] Me registro, veo mi dorsal una vez, el admin me aprueba y entro con mote + dorsal; la app sabe si soy admin o jugador.
- [ ] Un jugador no puede acceder a acciones de admin (probado con tests y llamando a la API directamente).
- [ ] Ningún jugador puede ver dorsales ni valoraciones de otros en la app ni en la API; solo el admin ve dorsales, y solo en su panel.
- [ ] Tras varios intentos fallidos de login, la cuenta se bloquea temporalmente.
- [ ] El admin crea un partido, elige 10 con el buscador y genera equipos Blanco (Nevados C.F.) y Negro (Sombras F.C.) con fuerza total parecida; "Rebarajar" da repartos distintos y equilibrados.
- [ ] Un jugador reporta goles y asistencias, el admin los confirma y suben a la clasificación ordenable.
- [ ] Valoro a un compañero una sola vez, no puedo editarlo ni verlo después, y nadie ve medias individuales.
- [ ] Si el servidor está dormido, la app muestra "Conectando…" y termina entrando sola.
- [ ] Varios móviles con el APK ven los mismos datos.
- [ ] El APK se instala en mi móvil, funciona contra el backend que corre en mi PC (etapa local) y una versión nueva se instala encima sin desinstalar.
- [ ] Todo lo de la sección 9.2 está preparado y documentado, y no se ha publicado ni contratado nada sin mi OK.
- [ ] Existe en la app y en la API el borrado de cuenta.
- [ ] Sin secretos en el repositorio.
