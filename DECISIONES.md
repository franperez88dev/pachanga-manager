# Decisiones y cambios respecto a PROMPT.md

Cuando esto y `PROMPT.md` se contradigan, **manda este archivo** (son cambios acordados después).

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

## Equipos
- Se muestran las fuerzas totales con números ("15,0 vs 14,5"). Se sabe que, rebarajando muchas veces, podrían deducirse medias aproximadas; se acepta a cambio del pique entre amigos.
- Tolerancia de "Rebarajar": 0,5 puntos sobre el mejor reparto posible (explicado en `backend/pachanga/equipos.py`).

## Pendiente de decidir más adelante
- Migraciones de base de datos (Flask-Migrate) antes de la Fase 4.
