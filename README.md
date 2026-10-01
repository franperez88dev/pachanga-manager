# Pachanga Manager

App Android para organizar los partidos de fútbol de la peña: convocatorias, equipos
equilibrados, votación para rebarajar, orden en portería, goles, clasificación y
valoraciones secretas.

| Carpeta / archivo | Qué es |
|---|---|
| `backend/` | La API (el "servidor"): Flask + SQLAlchemy. En local guarda los datos en SQLite. |
| `app/` | La app: React + Vite. Desde la Fase 3, también el proyecto Android (Capacitor). |
| `referencia/` | Prototipo y vista previa del diseño (no forman parte de la app). |
| `PROMPT.md` | El encargo original. |
| `DECISIONES.md` | Cambios acordados después. **Si contradice a `PROMPT.md`, manda `DECISIONES.md`.** |

> Este README cubre la **etapa local** (probar en el ordenador). En las Fases 3 a 5 se
> añadirá cómo generar el APK, instalarlo en el móvil, desplegar el backend y repartir versiones.

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

## 6. Resumen de comandos

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
| `app` | `npm run build` | Genera la versión final en `app/dist` (se usará en la Fase 3) |

---

## 7. Problemas frecuentes

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
