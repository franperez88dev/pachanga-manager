# Pachanga Manager

App Android para organizar los partidos de fútbol de la peña: convocatorias, equipos
equilibrados, votación para rebarajar, orden en portería, goles, clasificación y
valoraciones secretas.

| Carpeta / archivo | Qué es |
|---|---|
| `backend/` | La API (el "servidor"): Flask + SQLAlchemy. En local guarda los datos en SQLite. |
| `app/` | La app: React + Vite. En `app/android`, el proyecto Android (Capacitor) que genera el APK. |
| `recursos-play/` | Imágenes para la ficha de Google Play (se usarán al publicar). |
| `referencia/` | Prototipo y vista previa del diseño (no forman parte de la app). |
| `PROMPT.md` | El encargo original. |
| `DECISIONES.md` | Cambios acordados después. **Si contradice a `PROMPT.md`, manda `DECISIONES.md`.** |

> Este README cubre la **etapa local**: probar en el ordenador y en tu móvil con el backend
> corriendo en tu PC. Más adelante se añadirá cómo desplegar el backend y repartir el APK.

---

## 1. Antes de empezar

### Programas necesarios

| Programa | Para qué | Comprobar en una terminal |
|---|---|---|
| Python 3.11 o superior | el backend | `python --version` |
| Node.js 22 o superior | la app | `node -v` |
| Git (y GitHub Desktop) | guardar versiones | `git --version` |
| VS Code | editar y abrir terminales | — |

### Cuatro ideas que conviene tener claras

- **Terminal y carpeta.** Todos los comandos se escriben en una terminal de VS Code
  (menú **Terminal → New Terminal**), que se abre en la carpeta `pachanga-manager`; con
  `cd backend` o `cd app` entras en la subcarpeta que toque. Tiene que ser una terminal
  **PowerShell**: mira el apartado siguiente.
- **Entorno virtual de Python (`.venv`).** Es una carpeta con las librerías del backend,
  separadas de las de tu ordenador. Hay que **activarlo** en cada terminal nueva
  (`.\.venv\Scripts\Activate.ps1`); sabrás que está activo porque la línea empieza por `(.venv)`.
- **`.env` frente a `.env.example`** (¡importante!):
  - `backend/.env.example` es una **plantilla que SÍ se sube a git**. Nunca pongas ahí claves reales.
  - `backend/.env` es **tu copia privada**, con tu clave de verdad. **Nunca se sube a git**
    (está en `.gitignore`). Es la que lee el backend.
- **Dos programas a la vez.** Para usar la app en local tienen que estar encendidos el
  **backend** (puerto 5000) y la **app** (puerto 5173), cada uno en su propia terminal.

### La terminal tiene que ser PowerShell (no el "Símbolo del sistema")

VS Code puede abrir dos tipos de terminal en Windows, y este README está escrito para
**PowerShell**. Se distinguen por cómo empieza la línea:

| La línea empieza por… | Es… | ¿Vale? |
|---|---|---|
| `PS F:\GitHub\pachanga-manager>` | **PowerShell** | ✅ Sí |
| `F:\GitHub\pachanga-manager>` (sin `PS`) | **Símbolo del sistema** (cmd) | ❌ No: ahí los comandos `.ps1` abren el Bloc de notas en vez de ejecutarse |

Este proyecto ya trae un ajuste (`.vscode/settings.json`) para que las **terminales nuevas** se
abran en PowerShell. Si tienes alguna terminal antigua abierta en cmd, ciérrala con el icono
de la **papelera** del panel de terminales y abre otra con **Terminal → New Terminal**.

Para abrir una PowerShell a mano: en el panel de terminales, pulsa la **flechita ˅** que hay
junto al **+** y elige **PowerShell**.

> Los comandos `npm run ...` funcionan en las dos, pero el resto del README (activar el
> entorno de Python, etc.) necesita PowerShell.

### Cómo leer los comandos de este README

Los comandos van en recuadros grises. Se **copian tal cual**, se pegan en la terminal
(clic derecho → Pegar, o Ctrl+V) y se pulsa **Enter**. Lo que va detrás de `#` es un
comentario para ti: si lo pegas no pasa nada, la terminal lo ignora.

**¿Dónde estoy?** La terminal siempre muestra delante de lo que escribes la carpeta en la que
estás. Por ejemplo:

```text
PS F:\GitHub\pachanga-manager\app>
```

significa que estás en la carpeta `app`. Si un paso dice "en la carpeta `app`" y tu terminal
pone otra cosa, muévete primero (ver `cd` abajo).

| Trozo | Qué significa |
|---|---|
| `cd app` | **c**ambia de **d**irectorio: entra en la carpeta `app` (desde `pachanga-manager`). |
| `cd ..` | Sube a la carpeta de arriba (de `app` vuelves a `pachanga-manager`). |
| `.\algo.ps1` | Ejecuta el script `algo.ps1` que está **en esta carpeta** (`.\` = "aquí"). Solo en PowerShell. |
| `npm run movil:instalar` | Ejecuta la tarea `movil:instalar`, que está definida en `app/package.json`. Hay que estar en la carpeta `app`. |
| **Ctrl+C** | Detiene el programa que está funcionando en esa terminal (por ejemplo, el backend). |

---

## 2. Instalación (solo la primera vez)

### 2.1 Backend

En una terminal, desde la carpeta `pachanga-manager`:

```powershell
cd backend
python -m venv .venv                   # 1. Crea el entorno virtual (la carpeta .venv)
.\.venv\Scripts\Activate.ps1           # 2. Lo activa: verás "(.venv)" al principio de la línea
pip install -r requirements-dev.txt    # 3. Instala Flask, pytest y el resto de librerías
copy .env.example .env                 # 4. Crea TU .env copiando la plantilla
python -c "import secrets; print(secrets.token_urlsafe(48))"   # 5. Genera una clave aleatoria
```

6. Abre `backend/.env` en VS Code (**no** el `.env.example`), sustituye `cambia-esto` en la
   línea `SECRET_KEY=` por la clave que ha salido en el paso 5 y guarda.
7. Crea tu usuario de admin:

   ```powershell
   flask create-admin
   ```

   Te pide tu mote y (opcional) tu nombre real, y te muestra **tu PIN de 4 cifras**.
   **Apúntalo**: no se puede volver a consultar. Entrarás con **mote + PIN**.

> Si el paso 2 da un error rojo sobre "la ejecución de scripts está deshabilitada", mira
> el apartado [Problemas frecuentes](#7-problemas-frecuentes).

### 2.2 App

En **otra** terminal (botón **+** del panel de terminales), desde `pachanga-manager`:

```powershell
cd app
npm install                            # Descarga React, Vite, etc. en app/node_modules
```

---

## 3. Encender todo (cada vez que quieras usarlo)

**Terminal 1: backend**

```powershell
cd backend
.\.venv\Scripts\Activate.ps1           # activa el entorno virtual
flask run --debug                      # enciende la API en http://127.0.0.1:5000
```

- `--debug` hace que el backend **se reinicie solo** al guardar un cambio en el código
  y muestra errores detallados. Úsalo solo en tu ordenador, nunca en el servidor de verdad.
- Para comprobar que funciona, abre http://127.0.0.1:5000/health en el navegador:
  debe salir `{"estado":"ok"}`.
- Déjala abierta. Para apagarlo: **Ctrl+C** en esa terminal.

**Terminal 2: app**

```powershell
cd app
npm run dev                            # enciende la app en http://127.0.0.1:5173
```

- Abre http://127.0.0.1:5173 en el navegador. Los cambios en `app/src` se ven al momento.
- Para apagarla: **Ctrl+C**.

**Verla como en el móvil:** en el navegador pulsa **F12** (herramientas de desarrollo) y
luego **Ctrl+Shift+M** (vista de dispositivo). Arriba puedes elegir un modelo de móvil.

---

## 4. Tests automáticos

Con el entorno virtual activado, en `backend`:

```powershell
pytest                                 # ejecuta todos los tests (deben salir todos "passed")
pytest -v                              # igual, pero con el nombre de cada test
pytest tests/test_partidos.py          # solo los de un archivo
```

Comprueban, entre otras cosas, el algoritmo de equipos, el login con PIN y su bloqueo, que
un jugador no puede hacer cosas de admin, la privacidad de PINes y valoraciones, la
votación para rebarajar y el flujo completo de un partido. Usan una base de datos en
memoria: **no tocan tus datos**.

---

## 5. Probar la app a mano

### 5.1 Datos de prueba

Para no tener que registrar a 10 personas, en la terminal del backend (puedes apagarlo con
Ctrl+C, ejecutar el comando y volver a encenderlo):

```powershell
flask datos-demo
```

Crea **12 jugadores de prueba ya aprobados** (Feragi, Chuti, El Tanke, Rulo, Kike, Nino,
Josemi, Payo, Sergi, Toni, Manu y Guaje), **todos con el PIN `1111`**, y les pone
valoraciones al azar para que los equipos salgan equilibrados.

> Estos comandos de prueba solo funcionan con la base de datos SQLite local; en el servidor
> de verdad se niegan a ejecutarse.

### 5.2 Ser admin y jugador a la vez

La sesión se guarda en el navegador. Para tener dos sesiones a la vez:

- Ventana normal: entra con **tu mote + tu PIN** (admin).
- Ventana de **incógnito** (Ctrl+Shift+N): entra como un jugador de prueba, por ejemplo
  **Feragi + 1111**.




### 5.3 Guion de prueba completo

Sigue estos pasos en orden; al lado de cada uno, lo que deberías ver.

1. **Registro de un jugador nuevo** (ventana de incógnito → *Soy nuevo*): elige mote, prueba
   el editor de avatar y el botón 🎲 *Aleatorio*, pulsa *Unirme a la peña*.
   → Aparece su **PIN una sola vez** y después "Esperando aprobación del admin".
2. **Aprobar el alta** (ventana de admin → pestaña **Admin → Altas**; el globo rojo indica
   que hay algo pendiente). Pulsa *Aprobar*.
   → En unos segundos (o pulsando *Comprobar ahora*), el jugador nuevo entra solo.
3. **Crear un partido** (admin → **Partidos → + Nuevo**): día, hora y lugar.
4. **Convocatoria**: marca **exactamente 10** en la cuadrícula (prueba el buscador) y pulsa
   *Crear equipos*.
   → Aparece la **pista** con los dos equipos (portero, 2 defensas y 2 delanteros), la
   fuerza de cada equipo y el **orden en portería**. *Crear equipos* solo se puede hacer una vez.
5. **Votación para rebarajar**: como jugador convocado (incógnito), pulsa *Sí* o *No*.
   → Tu voto queda bloqueado hasta el siguiente reparto. Para no tener que entrar con 6
   cuentas, completa los votos con el comando de prueba (el número del partido es el que
   sale en la dirección del navegador, por ejemplo `#/partidos/1`):

   ```powershell
   flask demo-votar 1 --si 5           # 5 jugadores de prueba convocados votan "sí"
   ```

   → Recarga la página del admin: con **6 síes** se activa *Rebarajar*. Al pulsarlo salen
   equipos nuevos y empieza una votación nueva. Máximo **3 repartos** en total.
6. **Volver a elegir**: con los mismos 10, los equipos no cambian; si cambias a alguien,
   los equipos y la votación empiezan de cero.
7. **Cerrar el partido**: *Cerrar partido* → indica el resultado con − y +.
   → Se abre la **planilla**: goles y gpp (goles en propia puerta) de cada jugador. Si no
   cuadra con el resultado sale un aviso, pero deja guardar.
   - *Confirmar*: queda todo confirmado y sube a la clasificación.
   - *Sig.*: te la saltas y cada jugador apunta lo suyo.
8. **Un jugador apunta sus goles** (incógnito → el partido jugado → *Mis goles en este
   partido*). Prueba también a **anularlo** (doble toque en el botón rojo).
9. **Confirmar goles** (admin → **Admin → Goles**): *Confirmar* o *Descartar*.
   → Lo confirmado aparece en **Tabla** (ordenable por Goles, En propia y Partidos).
10. **Valorar** (pestaña *Valorar*): dale estrellas a un compañero.
    → Queda "Valorado ✓" y no se puede cambiar ni volver a ver.
11. **Perfil**: cambia tu avatar; prueba *Cerrar sesión*.
12. **PIN olvidado** (admin → **Admin → Peña → PIN nuevo**, dos toques).
    → Sale un PIN nuevo para pasárselo por WhatsApp; el antiguo deja de valer.
13. **Hacer admin a otro** (Admin → Peña → *Hacer admin*). Siempre tiene que quedar uno.
14. **Borrar cuenta** (con un jugador de prueba: Perfil → *Borrar mi cuenta*, dos toques).
    También existe la página web http://127.0.0.1:5000/borrar-cuenta (la que pedirá Google Play).
15. **"Conectando con el servidor…"**: apaga el backend (Ctrl+C) y recarga la app.
    → Sale esa pantalla y reintenta sola; al volver a encender el backend, entra sola.

### 5.4 Empezar de cero

Si quieres borrar todos los datos de prueba:

1. Apaga el backend (Ctrl+C).
2. Borra el archivo `backend/instance/pachanga.db`.
3. Vuelve a ejecutar `flask create-admin` (te dará un **PIN nuevo**) y, si quieres, `flask datos-demo`.

> Haz lo mismo si, tras actualizar el código, el backend da errores del tipo
> "no such column": la estructura de la base de datos ha cambiado y en la etapa local es
> más sencillo empezar de cero (antes de publicar añadiremos migraciones).

---

## 6. La app en tu móvil (APK de pruebas)

La app web de `app/` se mete dentro de una app Android con **Capacitor**. El resultado es un
**APK**: el archivo que se instala en el móvil. En esta etapa, el móvil habla con el backend
que corre en **tu PC** a través del **cable USB**.

Todo se hace con tres comandos, que se escriben en la carpeta `app` (por dentro usan el script `app/compilar-apk.ps1`):

| Lo que escribes (en la carpeta `app`) | Para qué sirve | Cuándo usarlo |
|---|---|---|
| `npm run movil:comprobar` | Dice si el móvil está bien conectado y si el backend está encendido. **No instala nada.** | Antes de instalar, o cuando algo no va. |
| `npm run movil:instalar` | Fabrica el APK con tu código actual y lo instala en el móvil. | La primera vez y cada vez que cambies algo de la app. |
| `npm run movil:conectar` | Vuelve a "enchufar" el móvil al backend del PC, sin fabricar nada. | Tras desenchufar el cable o reiniciar el PC o el móvil. |

### 6.1 Preparar el PC (solo la primera vez)

Ya está hecho en este ordenador. Lo dejo apuntado por si cambias de PC:

1. **Android Studio** con la **plataforma Android 16 (API 36)** y las **Build-Tools 36**
   (Android Studio → *More Actions* → **SDK Manager**: pestaña *SDK Platforms* para la
   plataforma; pestaña *SDK Tools*, con *Show Package Details* marcado, para las Build-Tools
   y las *Platform-Tools*).
2. **Un JDK 21** (Gradle no funciona con el Java 25 que trae Android Studio). Aquí está en
   `C:\Users\SuFran\.jdks\temurin-21...`. El script lo encuentra solo.
3. El **keystore** de la firma (apartado 6.5).

### 6.2 Preparar el móvil (solo la primera vez)

Pasos para tu **Samsung A52s** (en otras marcas los menús se llaman parecido):

1. **Activa el modo desarrollador:** *Ajustes → Acerca del teléfono → Información de
   software* y toca **7 veces seguidas** sobre **Número de compilación**. Te pedirá el PIN de
   desbloqueo y saldrá "Modo desarrollador activado".
2. **Activa la depuración USB:** vuelve a *Ajustes*; al final de la lista hay un menú nuevo,
   **Opciones de desarrollador**. Entra y activa **Depuración USB**.
3. **Conecta el móvil al PC con el cable USB.** Tiene que ser un cable de **datos**: algunos
   cables baratos solo cargan.
4. **Autoriza el PC:** con el móvil desbloqueado saldrá el aviso **"¿Permitir depuración
   USB?"**. Marca *Permitir siempre desde este ordenador* y pulsa **Permitir**. Si no sale,
   desenchufa y vuelve a enchufar el cable.

### 6.3 Probar la app en el móvil, paso a paso

Necesitas **dos terminales** en VS Code: una para el backend y otra para la app. Para abrir
una segunda terminal, pulsa el **+** que hay arriba a la derecha del panel de terminales.
Para pasar de una a otra, haz clic en su nombre en la lista de la derecha.

**Paso 1. Enciende el backend (terminal 1).** Si ya lo tienes encendido, sáltate este paso.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
flask run --debug
```

- `cd backend`: entra en la carpeta del backend. Si la terminal ya pone `...\backend>`, no hace falta.
- `.\.venv\Scripts\Activate.ps1`: activa el entorno de Python; la línea empezará por `(.venv)`.
- `flask run --debug`: enciende el backend. **Va bien** si al final pone
  `Running on http://127.0.0.1:5000`. Esta terminal se queda ocupada: **no la cierres**.

**Paso 2. Ve a la carpeta `app` (terminal 2).** Abre una terminal nueva con el **+**. Se abre en
`pachanga-manager`, así que escribe:

```powershell
cd app
```

La línea debe acabar en `...\pachanga-manager\app>`.

**Paso 3. Comprueba que todo está listo.** Con el móvil conectado por el cable:

```powershell
npm run movil:comprobar
```

**Va bien** si salen dos líneas verdes:

```text
OK  Móvil conectado y con la depuración USB autorizada.
OK  El backend está encendido.
```

Si alguna sale en amarillo con `NO`, el propio mensaje dice qué hacer (normalmente:
autorizar el PC en el aviso del móvil, o encender el backend). Arréglalo y repite este paso.

**Paso 4. Fabrica e instala la app.**

```powershell
npm run movil:instalar
```

Irán apareciendo muchas líneas. Los pasos importantes salen en verde, empezando por `==>`:

| Lo que ves | Qué está pasando |
|---|---|
| `==> Buscando el JDK y el SDK` | Comprueba que tienes las herramientas. |
| `==> Compilando la web para el móvil` | Prepara la app con la dirección del backend para el móvil. |
| `==> Copiando la web al proyecto Android` | Mete esa app dentro del proyecto Android. |
| `==> Generando el APK de pruebas` | Fabrica el APK y lo firma. **La primera vez tarda varios minutos**; después, menos de uno. Salen muchas líneas `> Task ...`: es normal. |
| `BUILD SUCCESSFUL` | El APK está fabricado. |
| `==> Instalando en el móvil` | Lo instala en el móvil por el cable, encima de la versión anterior si la hay (no borra tu sesión). |
| `Success` y `Instalada. Abre 'Pachanga Manager' en el móvil.` | **Terminado.** |

Si en lugar de eso sale una línea roja que empieza por `ERROR:`, lee lo que dice y mira el
apartado [8. Problemas frecuentes](#8-problemas-frecuentes).

**Paso 5. Abre la app en el móvil.** Busca el icono verde con un balón, **Pachanga Manager**.
Verás la pantalla verde de arranque, luego "Conectando con el servidor…" un instante y,
después, la pantalla para entrar. Entra con tu **mote y tu PIN** y sigue el
[guion de prueba del apartado 5.3](#53-guion-de-prueba-completo), esta vez en el móvil. Prueba
también el **botón "atrás"** de Android (vuelve a la pantalla anterior y, desde Inicio, sale
de la app) y a **girar el móvil** en la pista de los equipos.

**Paso 6. Cuando termines.** En la terminal 1 pulsa **Ctrl+C** para apagar el backend. Ya
puedes desenchufar el móvil. La app sigue instalada, pero sin el backend del PC se quedará en
"Conectando con el servidor…".

### 6.4 Las siguientes veces

| Situación | Qué hacer |
|---|---|
| Quiero volver a probar otro día | Paso 1 (encender backend), conectar el móvil, y en la carpeta `app`: `npm run movil:conectar`. No hace falta reinstalar. |
| He desenchufado el cable o he reiniciado el PC o el móvil, y la app se queda en "Conectando…" | `npm run movil:conectar` (con el backend encendido). |
| He cambiado código de la app (`app/src`) | `npm run movil:instalar` otra vez. Se instala encima y conservas la sesión. |
| He cambiado código del backend | Nada: con `flask run --debug` el backend se reinicia solo. |

> **¿Por qué hay que "volver a conectar"?** La app del móvil busca el backend en su propia
> dirección `127.0.0.1:5000`. El script le pide a Android (con `adb reverse`) que todo lo que
> vaya ahí lo mande por el cable a tu PC. Ese "desvío" se borra al desenchufar el cable o al
> reiniciar, y `npm run movil:conectar` lo vuelve a crear.

### 6.5 La firma del APK (¡importante!)

Android solo deja instalar una versión nueva **encima** de la que ya tienes si las dos están
**firmadas con la misma clave**. Esa clave es como el sello de la peña: demuestra que la
actualización viene del mismo sitio que la app original. Si algún día la pierdes, ningún
móvil aceptará tus actualizaciones. Cada colega tendría que **desinstalar la app** (perdiendo
su sesión) e instalar la nueva, y en Google Play **no podrías volver a actualizarla nunca**.

- **Dónde está la clave (el *keystore*):** `C:\Users\SuFran\.pachanga\pachanga.jks`, fuera del repositorio.
- **Su contraseña:** dentro de `app\android\keystore.properties`, que no se sube a git.
- **Qué hacer YA:** copia **esos dos archivos** a un sitio seguro fuera del PC: un pendrive
  que guardes, tu Google Drive personal, un gestor de contraseñas… Si se rompe el disco y no
  tienes copia, no hay forma de recuperarla.
- **Nunca** los subas a GitHub ni los mandes por WhatsApp.

El script firma con esa clave tanto la versión de pruebas como la versión final.

### 6.6 Número de versión

La versión está en **un solo sitio**: la línea `"version"` de `app/package.json`
(por ejemplo `"version": "0.1.0"`). Android necesita además un número entero que **siempre
suba** (`versionCode`), y se calcula solo: `0.1.0` → `100`, `1.2.3` → `10203`.

Para subirla, en la carpeta `app`:

```powershell
npm run version:subir         # 0.1.0 -> 0.1.1   (arreglos pequeños)
npm run version:subir-menor   # 0.1.1 -> 0.2.0   (novedades)
```

Súbela antes de fabricar una versión para repartir. Para tus pruebas no hace falta.

### 6.7 Instalarlo en el móvil de un colega (más adelante)

Cuando el backend esté en internet (Fase 4), el APK se podrá pasar por WhatsApp o Drive. Al
abrirlo, Android pedirá **permitir instalar apps de orígenes desconocidos** para WhatsApp,
Drive o el gestor de archivos que se use: hay que aceptarlo una vez. Por ahora no tiene
sentido, porque el backend solo existe en tu PC.

---

## 7. Resumen de comandos

| Dónde | Comando | Qué hace |
|---|---|---|
| `backend` | `.\.venv\Scripts\Activate.ps1` | Activa el entorno virtual (en cada terminal nueva) |
| `backend` | `flask run --debug` | Enciende la API en el puerto 5000 |
| `backend` | `pytest` | Ejecuta los tests |
| `backend` | `flask create-admin` | Crea el primer admin (solo si no hay ninguno) |
| `backend` | `flask datos-demo` | Solo pruebas: 12 jugadores con PIN 1111 |
| `backend` | `flask demo-votar N --si 5 --no 1` | Solo pruebas: votos en el partido N |
| `app` | `npm install` | Instala las dependencias (la primera vez o si cambia `package.json`) |
| `app` | `npm run dev` | Enciende la app en el puerto 5173 |
| `app` | `npm run build` | Genera la web final en `app/dist` |
| `app` | `npm run movil:comprobar` | Dice si el móvil está bien conectado y si el backend está encendido |
| `app` | `npm run movil:instalar` | Compila el APK de pruebas y lo instala en el móvil conectado por USB |
| `app` | `npm run movil:conectar` | Vuelve a conectar el móvil con el backend del PC (tras desenchufar el cable) |
| `app` | `npm run version:subir` | Sube la versión de la app (0.1.0 → 0.1.1) |

---

## 8. Problemas frecuentes

| Síntoma | Solución |
|---|---|
| Al activar el entorno: *"la ejecución de scripts está deshabilitada en este sistema"* | Ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y responde **S**. Permite ejecutar scripts locales como `Activate.ps1`. |
| `flask` o `pytest` *"no se reconoce como nombre de un cmdlet"* | No tienes el entorno virtual activado (falta `(.venv)` al principio): `.\.venv\Scripts\Activate.ps1`. |
| *"Falta SECRET_KEY"* al arrancar | No existe `backend/.env` o le falta la clave: repite los pasos 4 a 6 de la instalación. |
| La app se queda en *"Conectando con el servidor…"* | El backend está apagado: enciéndelo en la terminal 1 (`flask run --debug`). |
| *"Address already in use"* / puerto ocupado | Ya hay otro backend o app encendido: busca la otra terminal y páralo con Ctrl+C. |
| He cambiado código del backend y no se nota | Si no usas `--debug`, apágalo (Ctrl+C) y vuelve a encenderlo. |
| *"no such column"* u otros errores de base de datos | Ver [Empezar de cero](#54-empezar-de-cero). |
| He olvidado mi PIN de admin | Si hay otro admin, que te dé uno nuevo desde Admin → Peña. Si no, empieza de cero. |
| Al escribir un comando `.ps1` se abre el **Bloc de notas** y no pasa nada | Estás en el **Símbolo del sistema**, no en PowerShell: ver [La terminal tiene que ser PowerShell](#la-terminal-tiene-que-ser-powershell-no-el-símbolo-del-sistema). |
| `npm run movil:...` dice *"Missing script"* | No estás en la carpeta `app`: escribe `cd app` (o `cd ..\app` si estás en `backend`). |
| *"No encuentro un JDK entre la versión 17 y la 24"* | Falta el JDK 21: apartado [6.1](#61-preparar-el-pc-solo-la-primera-vez). |
| *"Falta la plataforma Android 36"* | Instálala desde el SDK Manager: apartado [6.1](#61-preparar-el-pc-solo-la-primera-vez). |
| El script dice `NO` sobre el móvil | Lee el mensaje amarillo: casi siempre es autorizar el PC en el aviso del móvil, activar la depuración USB o usar un cable de datos ([6.2](#62-preparar-el-móvil-solo-la-primera-vez)). Repite `npm run movil:comprobar` hasta que salga `OK`. |
| La app del móvil se queda en *"Conectando…"* | ¿Está `flask run` encendido? ¿Has desenchufado el cable? Ejecuta `npm run movil:conectar`. |
| *"INSTALL_FAILED_UPDATE_INCOMPATIBLE"* al instalar | Hay instalada una versión firmada con otra clave: desinstala la app del móvil una vez y vuelve a instalar. |
