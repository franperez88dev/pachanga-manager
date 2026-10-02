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
  (menú **Terminal → New Terminal**; es PowerShell). La terminal se abre en la carpeta
  `pachanga-manager`; con `cd backend` o `cd app` entras en la subcarpeta que toque.
  Si en algún momento no sabes dónde estás, escribe `pwd`.
- **Entorno virtual de Python (`.venv`).** Es una carpeta con las librerías del backend,
  separadas de las de tu ordenador. Hay que **activarlo** en cada terminal nueva
  (`.\.venv\Scripts\Activate.ps1`); sabrás que está activo porque la línea empieza por `(.venv)`.
- **`.env` frente a `.env.example`** (¡importante!):
  - `backend/.env.example` es una **plantilla que SÍ se sube a git**. Nunca pongas ahí claves reales.
  - `backend/.env` es **tu copia privada**, con tu clave de verdad. **Nunca se sube a git**
    (está en `.gitignore`). Es la que lee el backend.
- **Dos programas a la vez.** Para usar la app en local tienen que estar encendidos el
  **backend** (puerto 5000) y la **app** (puerto 5173), cada uno en su propia terminal.

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
**APK**: el archivo que se instala en el móvil. En esta etapa el móvil habla con el backend de
**tu PC** a través del **cable USB**.

### 6.1 Preparar el PC (solo la primera vez)

Además de Android Studio, para compilar hacen falta dos cosas que se descargan desde él.

**a) La plataforma Android 36**

1. Abre Android Studio (`F:\Android Studio\bin\studio64.exe`). Si es la primera vez, sigue el
   asistente con las opciones por defecto (*Standard*) y acepta las licencias.
2. En la pantalla de bienvenida: **More Actions → SDK Manager** (con un proyecto abierto:
   **File → Settings → Languages & Frameworks → Android SDK**).
3. Comprueba que arriba, en *Android SDK Location*, pone
   `C:\Users\SuFran\AppData\Local\Android\Sdk`.
4. Pestaña **SDK Platforms**: marca **Android 16 (API 36)**.
5. Pestaña **SDK Tools**: marca **Show Package Details** (abajo a la derecha) y, dentro de
   *Android SDK Build-Tools*, marca la versión **36** más alta. Marca también (o actualiza)
   **Android SDK Platform-Tools**.
6. **Apply → OK** y espera a que termine la descarga.

**b) Un JDK 21** (Android Studio trae Java 25, que el Gradle de Capacitor 8 no admite)

1. En Android Studio: **File → Open** y elige la carpeta `F:\GitHub\pachanga-manager\app\android`.
2. Al abrirlo intentará "sincronizar" y probablemente falle diciendo que la versión de Java
   no es compatible. Es normal.
3. Ve a **File → Settings → Build, Execution, Deployment → Build Tools → Gradle**.
4. En **Gradle JDK**, despliega la lista y elige **Download JDK…** → *Version* **21**,
   *Vendor* **Eclipse Temurin** → **Download**. Se guarda en `C:\Users\SuFran\.jdks\`.
5. **OK**, y luego el botón del elefante con flecha (**Sync Project with Gradle Files**).
   Esta vez debe terminar bien.

> Después puedes cerrar Android Studio: para compilar usaremos un script desde VS Code.
> Android Studio solo hacía falta para descargar estas dos cosas.

### 6.2 Preparar el móvil (solo la primera vez)

1. **Activar las opciones de desarrollador:** *Ajustes → Información del teléfono* y toca
   **7 veces** sobre **Número de compilación** (en algunos móviles está dentro de
   *Información de software*). Te pedirá tu PIN de desbloqueo y dirá "Ya eres desarrollador".
2. **Activar la depuración USB:** *Ajustes → Sistema → Opciones de desarrollador →*
   **Depuración USB**. En los Xiaomi activa también **Instalar vía USB**.
3. **Conecta el móvil al PC con un cable USB de datos** (algunos cables solo sirven para cargar).
4. En el móvil saldrá **"¿Permitir depuración USB?"**: marca *Permitir siempre desde este
   ordenador* y acepta.

Para comprobarlo, en una terminal:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices
```

Debe salir una línea con un código y la palabra `device`. Si pone `unauthorized`, mira el
aviso del paso 4 en el móvil.

### 6.3 Compilar, instalar y probar

1. **Terminal 1:** enciende el backend como siempre (apartado 3): `flask run --debug`.
2. **Terminal 2** (carpeta `app`), con el móvil conectado por USB:

   ```powershell
   .\compilar-apk.ps1 -Instalar
   ```

   El script va explicando cada paso mientras lo ejecuta:

   | Paso | Comando | Qué hace |
   |---|---|---|
   | 1 | — | Busca el JDK 21 y el SDK de Android |
   | 2 | `npm run build:movil` | Compila la web con la URL del backend para el móvil (`app/.env.movil`) |
   | 3 | `npx cap sync android` | Copia esa web dentro del proyecto Android |
   | 4 | `gradlew.bat assembleDebug` (en `app/android`) | Genera el APK firmado. **La primera vez tarda varios minutos** (descarga Gradle y librerías) |
   | 5 | `adb install -r ...` | Instala el APK en el móvil, encima de la versión anterior y sin borrar datos |
   | 6 | `adb reverse tcp:5000 tcp:5000` | Hace que el `127.0.0.1:5000` **del móvil** sea el backend **de tu PC**, por el cable |

   El APK queda en `app/android/app/build/outputs/apk/debug/app-debug.apk`.

3. Abre **Pachanga Manager** en el móvil y entra con tu mote y tu PIN.

**Cada vez que desconectes y vuelvas a conectar el cable** (o reinicies el PC o el móvil), el
paso 6 se pierde y la app se queda en "Conectando con el servidor…". Para recuperarlo sin
volver a compilar:

```powershell
.\compilar-apk.ps1 -SoloConectar
```

**Si cambias código de la app**, vuelve a ejecutar `.\compilar-apk.ps1 -Instalar`: se instala
encima y conservas la sesión. Los cambios del backend no necesitan reinstalar nada.

### 6.4 La firma del APK (¡importante!)

Android solo deja instalar una versión nueva **encima** de la que ya tienes si las dos están
**firmadas con la misma clave**. Esa clave es como el sello de la peña: demuestra que la
actualización viene del mismo sitio que la app original. Si algún día la pierdes, ningún
móvil aceptará tus actualizaciones. Cada colega tendría que **desinstalar la app** (perdiendo
su sesión) e instalar la nueva, y en Google Play **no podrías volver a actualizarla nunca**.

- **Dónde está:** `C:\Users\SuFran\.pachanga\pachanga.jks` (el *keystore*, fuera del repositorio).
- **Su contraseña:** en `app/android/keystore.properties` (no se sube a git).
- **Qué hacer YA:** copia **los dos archivos** a un sitio seguro fuera del PC: un pendrive
  que guardes, tu Google Drive personal, un gestor de contraseñas… Si se rompe el disco y no
  tienes copia, no hay forma de recuperarla.
- **Nunca** los subas a GitHub ni los mandes por WhatsApp.

Gradle usa esa misma firma para la versión de pruebas (debug) y para la final (release).

### 6.5 Número de versión

La versión está en **un solo sitio**: el campo `"version"` de `app/package.json`
(por ejemplo `0.1.0`). Android necesita además un número entero que **siempre suba**
(`versionCode`), y se calcula solo: `0.1.0` → `100`, `1.2.3` → `10203`.

```powershell
npm run version:subir         # 0.1.0 -> 0.1.1   (arreglos pequeños)
npm run version:subir-menor   # 0.1.1 -> 0.2.0   (novedades)
```

Súbela antes de compilar una versión para repartir. Para tus pruebas no hace falta.

### 6.6 Instalarlo en el móvil de un colega (más adelante)

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
| `app` | `.\compilar-apk.ps1 -Instalar` | Compila el APK de pruebas y lo instala en el móvil conectado por USB |
| `app` | `.\compilar-apk.ps1 -SoloConectar` | Vuelve a conectar el móvil con el backend del PC (tras desenchufar el cable) |
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
| `compilar-apk.ps1`: *"No encuentro un JDK entre la versión 17 y la 24"* | Falta el JDK 21: apartado [6.1 b](#61-preparar-el-pc-solo-la-primera-vez). |
| `compilar-apk.ps1`: *"Falta la plataforma Android 36"* | Instálala desde el SDK Manager: apartado [6.1 a](#61-preparar-el-pc-solo-la-primera-vez). |
| *"No hay ningún móvil conectado"* | Cable de datos (no solo de carga), depuración USB activada y aviso aceptado en el móvil ([6.2](#62-preparar-el-móvil-solo-la-primera-vez)). |
| La app del móvil se queda en *"Conectando…"* | ¿Está `flask run` encendido? ¿Has desenchufado el cable? Ejecuta `.\compilar-apk.ps1 -SoloConectar`. |
| *"INSTALL_FAILED_UPDATE_INCOMPATIBLE"* al instalar | Hay instalada una versión firmada con otra clave: desinstala la app del móvil una vez y vuelve a instalar. |
