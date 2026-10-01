# Pachanga Manager

App Android para organizar los partidos de fútbol de la peña: convocatorias, equipos
equilibrados, goles, clasificación y valoraciones secretas.

- `backend/`: API en Flask + SQLAlchemy (SQLite en local, PostgreSQL en producción).
- `app/`: React + Vite (y, desde la Fase 3, Capacitor para generar el APK).
- `DECISIONES.md`: cambios acordados respecto a `PROMPT.md` (si se contradicen, manda ese).

> Este README se completará en la Fase 5 (compilar el APK, desplegar, repartir versiones).

## Arrancar en local

Necesitas **dos terminales** abiertas a la vez (en VS Code: botón **+** del panel de terminal).

### Terminal 1: backend (carpeta `backend`)

La primera vez:

```powershell
cd backend
python -m venv .venv                      # crea el entorno virtual (solo la primera vez)
.\.venv\Scripts\Activate.ps1              # lo activa: verás "(.venv)" delante
pip install -r requirements-dev.txt       # instala Flask, pytest, etc.
copy .env.example .env                    # crea tu .env y pon una SECRET_KEY (ver dentro)
flask create-admin                        # crea tu usuario admin y te dice tu PIN (¡apúntalo!)
```

Cada vez que quieras arrancarlo:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
flask run                                 # API en http://127.0.0.1:5000 (Ctrl+C para parar)
```

Otros comandos útiles (con el entorno activado):

| Comando | Qué hace |
|---|---|
| `pytest` | Ejecuta todos los tests del backend |
| `flask datos-demo` | **Solo pruebas**: crea 12 jugadores de prueba (PIN `1111`) con valoraciones al azar |
| `flask demo-votar 2 --si 5` | **Solo pruebas**: los jugadores de prueba convocados en el partido 2 votan "sí" a rebarajar |

Para empezar de cero, borra `backend/instance/pachanga.db` y vuelve a hacer `flask create-admin`.

### Terminal 2: app (carpeta `app`)

```powershell
cd app
npm install        # solo la primera vez (o si cambia package.json)
npm run dev        # abre http://127.0.0.1:5173 en el navegador
```

La app usa la URL del backend de `app/.env.development` (`VITE_API_URL`).
Para verla como en el móvil: en el navegador pulsa **F12** y el icono de móvil (o Ctrl+Shift+M).
