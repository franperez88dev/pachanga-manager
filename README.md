# Pachanga Manager

Aplicación web para organizar los partidos de fútbol de la peña: cada uno reserva su hueco
(con reservas y multas por borrarse tarde), equipos equilibrados, votación para rebarajar,
orden en portería, goles, clasificación y valoraciones secretas. Se usa desde el navegador del móvil (Android o iPhone) y se puede
añadir a la pantalla de inicio como una app.

| Carpeta / archivo | Qué es |
|---|---|
| `backend/` | El servidor: Flask + SQLAlchemy. Contesta a la app (la API) y entrega la web compilada. Guarda los datos en SQLite. |
| `backend/pachanga/web/` | La web **ya compilada** (la genera `npm run build`). Se sube a git: es lo que publica el servidor. No se edita a mano. |
| `app/` | El código de la parte visual: React + Vite. |
| `referencia/` | Prototipo y vista previa del diseño (no forman parte de la app). |
| `PROMPT.md` | El encargo original. |
| `DECISIONES.md` | Cambios acordados después. **Si contradice a `PROMPT.md`, manda `DECISIONES.md`.** |

> Los apartados 1 a 5 son para trabajar y probar **en tu PC**. El apartado 6 explica cómo
> **publicarla en internet** (PythonAnywhere) para que la usen los colegas.

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
| `npm run build` | Ejecuta la tarea `build`, que está definida en `app/package.json`. Hay que estar en la carpeta `app`. |
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
- (El puerto 5000 también entrega la web, pero la **compilada** con `npm run build`, que es
  la que se publica. Mientras programas, usa siempre el 5173.)
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

Hay otros dos comandos de prueba para no tener que entrar con 10 cuentas distintas. El número
es el del partido: el que sale en la dirección del navegador (por ejemplo `#/partidos/1`).

```powershell
flask demo-apuntar 1                # los jugadores de prueba reservan hueco en el partido 1 (10 por defecto)
flask demo-apuntar 1 --cuantos 12   # ...o 12: los 10 primeros juegan y 2 quedan de reservas
flask demo-votar 1 --si 5           # 5 jugadores de prueba votan "sí" a rebarajar
```

> Estos comandos de prueba solo funcionan si tu `backend/.env` tiene `PERMITIR_DATOS_DEMO=1`
> (la plantilla ya lo trae). En el servidor de verdad no se pone, y se niegan a ejecutarse.

### 5.2 Ser admin y jugador a la vez

La sesión se guarda en el navegador. Para tener dos sesiones a la vez:

- Ventana normal: entra con **tu mote + tu PIN** (admin).
- Ventana de **incógnito** (Ctrl+Shift+N): entra como un jugador de prueba, por ejemplo
  **Feragi + 1111**.

> **No apuntes tus PINs en este README** (se sube a GitHub). Si quieres tenerlos a mano,
> usa el archivo `notas-privadas.md` de la raíz del proyecto: git lo ignora.

### 5.3 Guion de prueba completo

Sigue estos pasos en orden; al lado de cada uno, lo que deberías ver.

1. **Registro de un jugador nuevo** (ventana de incógnito → *Soy nuevo*): elige mote, prueba
   el editor de avatar y el botón 🎲 *Aleatorio*, pulsa *Unirme a la peña*.
   → Aparece su **PIN una sola vez** y después "Esperando aprobación del admin".
2. **Aprobar el alta** (ventana de admin → pestaña **Admin → Altas**; el globo rojo indica
   que hay algo pendiente). Pulsa *Aprobar*.
   → En unos segundos (o pulsando *Comprobar ahora*), el jugador nuevo entra solo.
3. **Crear un partido** (admin → **Partidos → + Nuevo**): día, hora, lugar y, si quieres, el
   **precio** (un texto libre, por ejemplo `Pagar a Feragi (2,2 € anticipado | 2,5 € el día
   del partido)`). El lugar y el precio salen ya rellenos con los del partido anterior.
   → Se abre la ficha del partido con la lista de **Apuntados (0/10)** vacía.
4. **Reservar hueco** (incógnito, como Feragi → el partido → *✋ Reservar hueco*).
   → Feragi aparece en la lista con el número **1)** y el aviso amarillo con el precio.
   Para llenar el partido sin entrar con más cuentas:

   ```powershell
   flask demo-apuntar 1 --cuantos 12
   ```

   → Recarga: la lista va numerada del **1) al 10)** (los que juegan) y, debajo, **Reservas:
   11) y 12)**. Quien entre ahora verá *✋ Apuntarme de reserva*.
5. **Liberar hueco** (incógnito → *Liberar hueco*, dos toques).
   → Feragi sale de la lista y **el primer reserva sube solo** al puesto 10.
   - Si faltan **más de 24 horas** para el partido: sin multa.
   - Si faltan **menos de 24 horas**: sale un aviso rojo antes de pulsar y, al confirmarlo,
     queda apuntada una **multa** (aunque un reserva ocupe el sitio). Para probarlo, crea un
     partido para dentro de unas horas. Los reservas se borran siempre sin multa.
6. **El admin gestiona la lista** (ventana de admin → el partido): cada fila tiene una **✕**
   para quitar a ese jugador (*Quitar* o *Quitar con multa*), y debajo un desplegable para
   **apuntar a alguien** (por ejemplo, a quien avisa por WhatsApp).
7. **Crear equipos** (admin, cuando hay 10): *⚙️ Crear equipos*.
   → Aparece la **pista** con los dos equipos (portero, 2 defensas y 2 delanteros), la
   fuerza de cada equipo y el **orden en portería**. *Crear equipos* solo se puede hacer una
   vez y **cierra la lista**: los jugadores ya no pueden apuntarse ni borrarse. Si alguien
   se cae, el admin lo quita con la ✕: entra el primer reserva y hay que crear los equipos otra vez.
8. **Votación para rebarajar**: como jugador que juega (incógnito), pulsa *Sí* o *No*.
   → Tu voto queda bloqueado hasta el siguiente reparto. Completa los votos con:

   ```powershell
   flask demo-votar 1 --si 5
   ```

   → Recarga la página del admin: con **6 síes** se activa *Rebarajar*. Al pulsarlo salen
   equipos nuevos y empieza una votación nueva. Máximo **3 repartos** en total.
9. **Multas** (admin → **Admin → Multas**): cada multa se marca como *Pagada* o se *Perdona*
   (y *Deshacer* si te equivocas). El jugador ve las suyas en **Perfil → Mis multas**, y en
   Inicio le sale un aviso mientras tenga alguna pendiente.
10. **Cerrar el partido**: *Cerrar partido* → indica el resultado con − y +.
    → Se abre la **planilla**: goles y gpp (goles en propia puerta) de cada jugador. Si no
    cuadra con el resultado sale un aviso, pero deja guardar.
    - *Confirmar*: queda todo confirmado y sube a la clasificación.
    - *Sig.*: te la saltas y cada jugador apunta lo suyo.
11. **Un jugador apunta sus goles** (incógnito → el partido jugado → *Mis goles en este
    partido*). Prueba también a **anularlo** (doble toque en el botón rojo).
12. **Confirmar goles** (admin → **Admin → Goles**): *Confirmar* o *Descartar*.
    → Lo confirmado aparece en **Tabla** (ordenable por Goles, En propia y Partidos).
13. **Valorar** (pestaña *Valorar*): dale estrellas a un compañero.
    → Queda "Valorado ✓" y no se puede cambiar ni volver a ver.
14. **Tema claro / oscuro**: pulsa el botón del **sol o la luna** (arriba a la derecha).
    → Cambia el color de toda la app y se queda guardado en ese móvil. Si nunca lo pulsas,
    la app usa el tema que tenga el móvil.
15. **Perfil**: cambia tu avatar; prueba *Cerrar sesión*.
16. **PIN olvidado** (admin → **Admin → Peña → PIN nuevo**, dos toques).
    → Sale un PIN nuevo para pasárselo por WhatsApp; el antiguo deja de valer.
17. **Hacer admin a otro** (Admin → Peña → *Hacer admin*). Siempre tiene que quedar uno.
18. **Borrar cuenta** (con un jugador de prueba: Perfil → *Borrar mi cuenta*, dos toques).
    También existe la página web http://127.0.0.1:5000/borrar-cuenta, para borrarla sin entrar en la app.
19. **"Conectando con el servidor…"**: apaga el backend (Ctrl+C) y recarga la app.
    → Sale esa pantalla y reintenta sola; al volver a encender el backend, entra sola.

### 5.4 Empezar de cero

Si quieres borrar todos los datos de prueba:

1. Apaga el backend (Ctrl+C).
2. Borra el archivo `backend/instance/pachanga.db`.
3. Vuelve a ejecutar `flask create-admin` (te dará un **PIN nuevo**) y, si quieres, `flask datos-demo`.

> **No hace falta borrar nada al actualizar el código.** Si una versión nueva necesita campos
> nuevos en la base de datos, el backend los añade solo al arrancar, sin tocar los datos que
> ya hay (lo hace `backend/pachanga/migraciones.py`).

---

## 6. Publicar la app en internet (PythonAnywhere)

La app es una **página web**: los colegas la abren en el navegador del móvil y, si quieren,
la añaden a la pantalla de inicio para que tenga su icono como cualquier app (apartado 6.5).
Funciona igual en Android y en iPhone, y no hay que instalar ni actualizar nada: cuando
publicas un cambio, todos lo ven la próxima vez que la abren.

El servidor es **PythonAnywhere** (plan gratuito). El recorrido de cada cambio es siempre el mismo:

```text
  TU PC                          GITHUB                       PYTHONANYWHERE
  cambias el código      --->    subes los cambios    --->    los descargas (git pull)
  npm run build                  (GitHub Desktop)             y pulsas "Reload"
```

En PythonAnywhere **no se compila nada**: `npm run build` (en tu PC) deja la web lista en
`backend/pachanga/web`, esa carpeta se sube a GitHub con el resto, y el mismo programa de
Python (Flask) entrega la web y contesta a la app.

### 6.1 Antes de publicar: compilar y subir a GitHub (en tu PC)

1. **Compila la web** (terminal en la carpeta `app`):

   ```powershell
   npm run build
   ```

   **Va bien** si termina con `✓ built in ...`. Crea o actualiza la carpeta `backend/pachanga/web`.

2. **Prueba la versión compilada** antes de publicarla. Con el backend encendido
   (`flask run --debug` en `backend`), abre **http://127.0.0.1:5000** (ojo: puerto **5000**,
   no el 5173). Es exactamente lo que verán tus colegas.

3. **Sube los cambios a GitHub** con GitHub Desktop: escribe un resumen del cambio,
   pulsa **Commit to main** y luego **Push origin**.

4. **El repositorio tiene que ser público** para que PythonAnywhere pueda descargarlo sin
   contraseñas (solo hay que hacerlo una vez): en github.com abre el repositorio →
   **Settings** → baja hasta **Danger Zone** → **Change repository visibility** → **Public**.

   > Al hacerlo público cualquiera puede leer el código. No contiene claves ni datos de la
   > peña (eso vive en el `.env` y en la base de datos, que nunca se suben). Sí se ven el
   > nombre y el correo con los que firmas los commits.

### 6.2 Montar la web en PythonAnywhere (solo la primera vez)

**Paso 1. Crea la cuenta.** En https://www.pythonanywhere.com → **Pricing & signup** →
**Create a Beginner account** (gratuita). El **nombre de usuario** que elijas será la
dirección de la app: `https://TU_USUARIO.pythonanywhere.com`. En todo lo que sigue,
cambia `TU_USUARIO` por ese nombre.

**Paso 2. Abre una consola.** Arriba, pestaña **Consoles** → en *Start a new console* pulsa
**Bash**. Se abre una terminal de Linux **en el servidor** (no en tu PC). Los comandos se pegan
con Ctrl+V (o clic derecho → Pegar) y se ejecutan con Enter.

**Paso 3. Descarga el código y prepara Python.** Pega estos comandos **uno a uno**:

```bash
git clone https://github.com/franperez88dev/pachanga-manager.git
```
Descarga el proyecto a la carpeta `pachanga-manager`. **Va bien** si acaba sin la palabra `fatal`.

```bash
mkvirtualenv --python=/usr/bin/python3.13 pachanga
```
Crea un entorno virtual llamado `pachanga` (como el `.venv` de tu PC). Al terminar, la línea
empezará por `(pachanga)`.

```bash
pip install -r pachanga-manager/backend/requirements.txt
```
Instala Flask y el resto de librerías. Tarda un minuto. **Va bien** si acaba con `Successfully installed ...`.

**Paso 4. Crea el `.env` del servidor.** Pega estas dos líneas:

```bash
cd ~/pachanga-manager/backend
printf 'SECRET_KEY=%s\nCORS_DESARROLLO=0\nCONFIAR_EN_PROXY=1\n' "$(python -c 'import secrets; print(secrets.token_urlsafe(48))')" > .env
```

La segunda crea el archivo `.env` con tres ajustes:

| Ajuste | Qué hace |
|---|---|
| `SECRET_KEY=...` | Una clave aleatoria nueva, **distinta de la de tu PC**, generada en el momento. |
| `CORS_DESARROLLO=0` | En el servidor no hace falta el permiso que usa Vite en tu PC. |
| `CONFIAR_EN_PROXY=1` | Para ver la IP real de cada móvil. **Imprescindible**: sin esto, el bloqueo por intentos fallidos bloquearía a toda la peña a la vez. |

Para comprobarlo: `cat .env` debe mostrar esas tres líneas.

**Paso 5. Crea tu usuario admin en el servidor:**

```bash
flask create-admin
```

Te pide tu mote y tu nombre real, y te muestra **tu PIN**. **Apúntalo** (en `notas-privadas.md`,
no en este README): es distinto del que usas en tu PC, porque el servidor tiene su propia
base de datos, vacía.

**Paso 6. Crea la web.** Pestaña **Web** → **Add a new web app** → **Next** →
elige **Manual configuration** (no "Flask") → **Python 3.13** → **Next**.

**Paso 7. Configúrala.** En esa misma pestaña **Web**, bajando por la página:

1. **Code → Source code:** escribe `/home/TU_USUARIO/pachanga-manager/backend`
2. **Code → WSGI configuration file:** pulsa el enlace (acaba en `_wsgi.py`). Se abre un
   editor: **borra todo** lo que haya y pega esto (cambiando `TU_USUARIO`):

   ```python
   import sys

   ruta = "/home/TU_USUARIO/pachanga-manager/backend"
   if ruta not in sys.path:
       sys.path.insert(0, ruta)

   from wsgi import application
   ```

   Pulsa **Save** (arriba a la derecha) y vuelve a la pestaña **Web**. Este archivo le dice a
   PythonAnywhere dónde está el proyecto y que arranque lo que hay en `backend/wsgi.py`.
3. **Virtualenv:** escribe `pachanga` y pulsa el ✔. Se convertirá en
   `/home/TU_USUARIO/.virtualenvs/pachanga`.
4. **Static files:** añade una fila con **URL** `/assets/` y **Directory**
   `/home/TU_USUARIO/pachanga-manager/backend/pachanga/web/assets`. Así las imágenes y el
   JavaScript los entrega PythonAnywhere directamente, sin gastar tu cupo de CPU.
5. **Security → Force HTTPS:** actívalo (**Enabled**).
6. Arriba del todo, pulsa el botón verde **Reload TU_USUARIO.pythonanywhere.com**.

**Paso 8. Pruébala.** Abre `https://TU_USUARIO.pythonanywhere.com` en el navegador del PC y
en el móvil. Debe salir la pantalla de entrar: entra con tu mote y el PIN del paso 5.

> Si sale **"Something went wrong"**: en la pestaña **Web**, abre el **Error log** y mira las
> últimas líneas (apartado [8. Problemas frecuentes](#8-problemas-frecuentes)).

### 6.3 Publicar un cambio (cada vez)

1. **En tu PC**, si has tocado algo de `app/`: `npm run build` en la carpeta `app`.
   (Si solo has tocado el backend, no hace falta.)
2. **En tu PC**: commit y **Push origin** con GitHub Desktop.
3. **En PythonAnywhere**, pestaña **Consoles** → abre tu consola Bash y pega:

   ```bash
   cd ~/pachanga-manager && git pull
   ```

   **Va bien** si lista los archivos cambiados (o dice `Already up to date` si no había nada).
4. Pestaña **Web** → botón verde **Reload**.

Para saber si el móvil ya ve la versión nueva, mira **Perfil**: abajo pone el número de
versión. Si quieres que cambie con cada publicación, súbelo antes del paso 1 con
`npm run version:subir` (en `app`).

> Lo que más se olvida es el **`npm run build`**: si no lo haces, el servidor seguirá
> entregando la web antigua aunque hayas subido el código nuevo.
>
> Si el cambio añade librerías a `backend/requirements.txt`, después del `git pull` ejecuta
> también: `workon pachanga && pip install -r backend/requirements.txt`

### 6.4 Mantenimiento

- **Renovar cada mes (¡importante!).** En el plan gratuito la web **se desactiva si no la
  renuevas**: una vez al mes entra en la pestaña **Web** y pulsa el botón amarillo
  **Run until 1 month from today**. PythonAnywhere avisa por correo unos días antes; ponte
  además un recordatorio en el calendario.
- **Copia de seguridad.** Todos los datos de la peña están en **un solo archivo**:
  `backend/instance/pachanga.db`. Para guardarlo: pestaña **Files** → entra en
  `pachanga-manager/backend/instance/` → icono de descarga junto a `pachanga.db`.
  Hazlo de vez en cuando (y siempre antes de publicar un cambio grande).
- **Si un cambio modifica la estructura de la base de datos** (campos nuevos), el servidor
  la actualiza solo al pulsar **Reload**: añade lo que falte sin borrar ni cambiar ningún
  dato (`backend/pachanga/migraciones.py`). Aun así, **descarga antes la copia de seguridad**
  del punto anterior: si algo saliera mal, bastaría con volver a subir ese archivo.
- **La hora de los partidos.** El servidor va con otro reloj (UTC), pero la app calcula las
  "24 horas antes del partido" con la hora de España. Si algún día la peña juega en otro
  huso horario, se cambia con `ZONA_HORARIA` en el `.env` del servidor.
- **Límites del plan gratuito:** 100 segundos de CPU al día (de sobra para una peña) y
  512 MB de disco. Si algún día se queda corto, el plan de pago quita la renovación mensual.
- **Los comandos de prueba (`flask datos-demo`) no funcionan en el servidor** a propósito:
  crearían jugadores con un PIN que conoce todo el mundo.

### 6.5 Cómo la usan tus colegas

Pásales el enlace `https://TU_USUARIO.pythonanywhere.com`. Para tenerla como una app:

- **Android (Chrome):** menú **⋮** → **Añadir a pantalla de inicio** (o **Instalar aplicación**).
- **iPhone (Safari):** botón **Compartir** → **Añadir a pantalla de inicio**.

Aparece el icono verde del balón y se abre a pantalla completa, sin la barra del navegador.
Cada uno se registra con su mote, elige avatar, **apunta su PIN** y espera a que lo apruebes
desde **Admin → Altas**.

---

## 7. Resumen de comandos

| Dónde | Comando | Qué hace |
|---|---|---|
| `backend` | `.\.venv\Scripts\Activate.ps1` | Activa el entorno virtual (en cada terminal nueva) |
| `backend` | `flask run --debug` | Enciende la API en el puerto 5000 |
| `backend` | `pytest` | Ejecuta los tests |
| `backend` | `flask create-admin` | Crea el primer admin (solo si no hay ninguno) |
| `backend` | `flask datos-demo` | Solo pruebas: 12 jugadores con PIN 1111 |
| `backend` | `flask demo-apuntar N --cuantos 12` | Solo pruebas: los jugadores de prueba reservan hueco en el partido N |
| `backend` | `flask demo-votar N --si 5 --no 1` | Solo pruebas: votos en el partido N |
| `app` | `npm install` | Instala las dependencias (la primera vez o si cambia `package.json`) |
| `app` | `npm run dev` | Enciende la app en el puerto 5173 (para programar) |
| `app` | `npm run build` | Compila la web y la deja en `backend/pachanga/web` (hazlo antes de publicar) |
| `app` | `npm run version:subir` | Sube la versión de la app (0.1.0 → 0.1.1); se ve en Perfil |
| PythonAnywhere | `cd ~/pachanga-manager && git pull` | Descarga en el servidor lo último de GitHub (y luego **Reload** en la pestaña Web) |
| PythonAnywhere | `workon pachanga` | Activa el entorno virtual del servidor en una consola nueva |

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
| `npm run ...` dice *"Missing script"* | No estás en la carpeta `app`: escribe `cd app` (o `cd ..\app` si estás en `backend`). |
| En http://127.0.0.1:5000 sale *"La app web todavia no esta compilada"* | Falta compilar: en la carpeta `app`, `npm run build`. |
| `flask datos-demo` dice *"solo para pruebas en tu PC"* | Falta `PERMITIR_DATOS_DEMO=1` en tu `backend/.env` (solo en tu PC, nunca en el servidor). |
| **PythonAnywhere:** *"Something went wrong"* | Pestaña **Web** → **Error log** (las últimas líneas dicen qué falla). Lo más habitual: `TU_USUARIO` mal escrito en el archivo WSGI o en *Source code*, el *Virtualenv* sin poner, o que falta el `.env` (paso 4 de [6.2](#62-montar-la-web-en-pythonanywhere-solo-la-primera-vez)). Tras corregir, **Reload**. |
| **PythonAnywhere:** he publicado y sigo viendo la versión antigua | ¿Hiciste `npm run build` antes del commit? ¿`git pull` en el servidor? ¿**Reload**? Mira la versión en Perfil. |
| **PythonAnywhere:** la web ha dejado de funcionar "de repente" | Seguramente ha caducado: pestaña **Web** → **Run until 1 month from today** ([6.4](#64-mantenimiento)). |
| **PythonAnywhere:** `git pull` dice que hay cambios locales o conflictos | En el servidor no se edita código. Para descartar lo tocado allí: `git checkout -- .` y repite el `git pull` (no afecta ni al `.env` ni a la base de datos). |
