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

## Asistencias ocultas (01/10/2026)
- **De momento solo se llevan goles (y gpp).** La app no muestra ni pide asistencias.
- El backend las conserva como campo opcional (vale 0 si no llega) para poder reactivarlas sin migrar datos.

## Avatares (01/10/2026)
- Cada jugador elige su avatar al registrarse y puede cambiarlo cuando quiera desde su perfil.
- **Personalizable**: color de piel, peinado + color (calvo, corto, tupé, rizos, melena o cresta), barba + color (sin barba, bigote, perilla o completa; la "de 3 días" se quitó porque quedaba mal).
- **Botón "Aleatorio"**, que se puede pulsar las veces que quiera; a veces sale un dibujo especial (alien, perro, gato, pepino, calabaza).
- Si no elige nada, le toca uno al azar.
- **El admin puede subir avatares nuevos** (PNG, JPEG o WebP de hasta 300 KB; SVG no, por seguridad). Al retirarlos desaparecen del catálogo, pero quien ya los tenga los conserva.

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

## Pendiente de decidir más adelante
- Migraciones de base de datos (Flask-Migrate) antes de la Fase 4.
