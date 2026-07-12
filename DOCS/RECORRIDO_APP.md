# Recorrido de la web — MarketMind AI (para explicarle a un compañero)

Esto es una guía rápida, sección por sección, para que alguien del equipo que no ha visto la web todavía entienda qué es cada parte, qué significan los términos que aparecen, dónde entran los dos agentes de IA, y cómo se completan las tareas que pide el hackathon (HU1, HU2, HU3).

Web en vivo: **https://marketmind-ai-three.vercel.app**
Para términos financieros/técnicos más al detalle (uno por uno), ver [`GLOSARIO.md`](GLOSARIO.md) en esta misma carpeta.

**Los dos agentes del proyecto**, para tenerlos presentes en todo el recorrido:
- **Analista de Coyuntura de Mercados IA** — lee una noticia + el movimiento de precio y genera una **señal** explicable (impacto + confianza + evidencia). Corre en **AI Analysis**.
- **Asesor Financiero e Inversiones IA** — toma esa señal y arma un **briefing** con una acción de investigación sugerida + una tarea para un humano. Corre en **Executive Briefing**.

Ninguno de los dos ejecuta ni sugiere compras/ventas — es una regla dura del proyecto, por eso todo termina en "acción de investigación" o "tarea", nunca en una orden.

---

## 1. Dashboard ("Financial Market Intelligence")

Es la pantalla de inicio — un resumen de todo lo que ha pasado en la app hasta el momento. No genera nada nuevo, solo agrupa lo que ya se generó en las otras páginas.

**Qué significa cada cosa:**
- **Badge arriba a la derecha** (ej. "Gemini en vivo" / "Modo mock") — indica si el análisis que estás viendo lo generó un LLM real o el modo de prueba con reglas fijas. Pásale el mouse encima para ver el detalle.
- **Noticias analizadas** — cuántas noticias distintas ya tienen al menos una señal generada por el Analista.
- **Activos monitoreados** — cuántos instrumentos (acciones, cripto, bonos, etc.) tiene la app en total.
- **Señales positivas** — cuántas de las señales generadas hasta ahora clasificaron el impacto como "positivo".
- **Track record** — de las señales generadas, qué % la dirección que clasificó el Analista (positivo/negativo/neutral) coincidió con el movimiento de precio real que se le mostró. No es una predicción a futuro, es una forma de auditar que el agente no está "alucinando" una dirección contraria a la evidencia que tuvo enfrente.
- **Actividad reciente** — tabla con las últimas 5 señales generadas (activo, impacto, confianza, estado de revisión).
- **Distribución de sentimiento** — el donut que muestra cuántas señales son positivas/negativas/neutrales/inciertas en total.

**Agentes:** ninguno corre aquí directamente — esta pantalla solo muestra resultados de lo que ya generaron el Analista y el Asesor en otras páginas.

---

## 2. News Radar (HU1)

El "feed" de noticias — la materia prima que van a leer los agentes. Es puramente informativo, todavía no hay IA involucrada.

**Qué significa cada cosa:**
- Cada tarjeta de noticia muestra: **fuente** (Reuters, Bloomberg, CoinDesk, etc.), **fecha/antigüedad**, y los **instrumentos** que menciona.
- **Filtros** (tipo de instrumento, activo específico, antigüedad en días) y la **barra de búsqueda** de arriba — para encontrar noticias puntuales.
- Botón **"Ver análisis"** en cada tarjeta — te lleva a AI Analysis con esa noticia + instrumento ya preseleccionados.

**Agentes:** ninguno corre aquí — es solo el catálogo de noticias que después el Analista va a leer.

**Cómo se "completa" esta parte:** no hay nada que completar, es de solo lectura. Su función es dejarte encontrar la noticia que quieres analizar.

---

## 3. AI Analysis (HU2) — aquí corre el Analista

Eliges una noticia + un instrumento, le das a generar, y el **Analista de Coyuntura de Mercados IA** produce una señal explicable.

**Qué significa cada cosa:**
- **Impacto** — positivo / negativo / neutral / incierto.
- **Anillo de confianza** — qué tan seguro está el modelo de su propia clasificación (no es una garantía de que el precio se vaya a mover así).
- **Evidencia** — 2 a 4 puntos concretos que cita el Analista, basados solo en la noticia y el precio que se le dieron (no puede inventar datos externos).
- **Comparación de precio** (con su mini-gráfico / sparkline) — cuánto se movió realmente el precio del instrumento alrededor de la fecha de la noticia.
- **Acción de investigación sugerida** — algo para que un humano revise (nunca "comprar" o "vender").
- **Disclaimer** — el aviso de que esto es informativo, no asesoría financiera personalizada.
- **Observaciones del analista** — el panel donde vos (como humano) escribís tu propia nota y decidís el estado: **Revisada** / **Escalada** / **Descartada**. Al darle **Guardar** se colapsa mostrando "✓ Guardado correctamente"; hay un botón **Editar** para volver a cambiarlo cuando sea.
- **Señales generadas** (lista de abajo) — todas las señales que ya se generaron, de cualquier instrumento. Hacer clic en cualquiera (esté "pending" o ya revisada) la vuelve a cargar arriba para verla o revisarla de nuevo.

**Agentes:** el **Analista** corre cada vez que le das a "Generar análisis". Si repetís la misma combinación de noticia+instrumento, no se genera una señal duplicada — se reusa la que ya existe (para no gastar cuota de IA de gratis).

**Cómo se completa la tarea acá:** generar el análisis → leer el resultado → escribir una observación y elegir un estado (Revisada/Escalada/Descartada) → Guardar. Eso es "la revisión humana" que pide el hackathon (HU3), y se puede hacer sobre cualquier señal en cualquier momento, no solo la primera vez.

---

## 4. Executive Briefing (HU3) — aquí corre el Asesor

Elegís una **watchlist** (grupo de instrumentos) y le das a generar — el **Asesor Financiero e Inversiones IA** arma un resumen ejecutivo por cada instrumento de esa lista que tenga noticias, y crea una **tarea** para seguimiento humano.

**Qué significa cada cosa:**
- Selector de **watchlist** — incluye una opción **"Todos"** que junta todos los instrumentos de la app.
- Cada tarjeta: noticia, movimiento de precio, **acción de investigación** (del Asesor, no del Analista) y un **resumen ejecutivo** de 2-3 puntos.
- El mismo panel de **Observaciones del analista** que en AI Analysis — revisar la señal desde acá también cuenta.
- Botón **"Descargar (.md)"** — baja el briefing completo como archivo Markdown, como si fuera el reporte que un analista se lleva para seguir trabajando fuera de la web.
- Panel **Tareas / Alertas** (a la derecha) — cada tarea generada por el Asesor. Se puede **"Marcar como hecha"** / **"Reabrir"**, y el botón **"Ver análisis"** te lleva directo a la señal completa en AI Analysis.

**Agentes:** el **Asesor** corre cada vez que generás un briefing. Si la señal de ese instrumento+noticia ya existía (porque la generaste antes en AI Analysis, o en un briefing anterior), no se vuelve a llamar al Analista — solo corre el Asesor sobre la señal existente y crea/reusa la tarea. Esto también evita duplicar tareas si generás el mismo briefing dos veces.

**Ojo con esto:** no todas las señales de "AI Analysis" tienen una tarea acá — solo las que pasaron por un briefing. Si generaste una señal directo en AI Analysis y nunca generaste el briefing de una watchlist que incluya ese instrumento, esa señal no va a tener tarea asociada (pero sí se puede revisar igual, desde AI Analysis).

**Cómo se completa la tarea acá:** generar el briefing → revisar cada señal (igual que en AI Analysis) → marcar las tareas como hechas cuando el seguimiento esté resuelto.

---

## 5. Active Watchlist

Una vista tipo "mercado" (parecida a Google Finance o CoinMarketCap) — no es un requisito mínimo del hackathon, es un extra que agregamos para que se vea más profesional.

**Qué significa cada cosa:**
- **Sentimiento de cartera** — el impacto más frecuente entre las señales generadas de esa watchlist.
- **Top mover** — el instrumento que más se movió (en % absoluto) en el último día.
- **Señales generadas (X / Y)** — cuántos de los instrumentos de la watchlist ya tienen una señal del Analista, sobre el total.
- **Volatilidad promedio** — el promedio de cuánto se mueven los precios de esa lista (más alto = más movimiento/riesgo).
- Tabla: precio actual, cambio del día, **sparkline de 14 días**, la señal IA (si existe) y su confianza.
- Botón **"Analizar"** — te lleva a AI Analysis con ese instrumento ya preseleccionado, para generar (o ver) su señal.

**Agentes:** ninguno corre aquí directamente — muestra el resultado de señales ya generadas en AI Analysis, si existen.

---

## Cómo se conecta todo (de principio a fin)

1. **News Radar** — encontrás una noticia interesante.
2. **AI Analysis** — generás la señal (corre el **Analista**), la revisás (Revisada/Escalada/Descartada + observación).
3. **Executive Briefing** — generás el briefing de la watchlist que incluya ese instrumento (corre el **Asesor**), que crea una **tarea**.
4. La tarea aparece en el panel de Tareas — la marcás como hecha cuando termine el seguimiento, o volvés a "Ver análisis" cuando quieras revisarla de nuevo.
5. **Dashboard** y **Active Watchlist** — reflejan todo lo anterior como resumen, sin generar nada nuevo por sí mismos.
