# Guion de video — MarketMind AI (Track 5)

Guion para 4 personas, ~3 minutos totales. Cada bloque trae el texto exacto para leer y qué mostrar en pantalla al mismo tiempo (grabado con OBS sobre **https://marketmind-ai-three.vercel.app**). Los tiempos son aproximados a un ritmo de habla normal (~150 palabras/min) — conviene ensayar una vez con cronómetro antes de grabar en serio.

---

## Persona 1 — Intro (0:00 – 0:35)

**[PANTALLA: Dashboard, recién cargado]**

> "Hola, somos [nombre del equipo] y este es **MarketMind AI**, nuestro proyecto para el **Track 5** del hackathon: Inteligencia de Mercado y Recomendaciones Informadas por Noticias.
>
> El problema que resolvemos es simple: un analista financiero recibe cientos de noticias al día y no tiene tiempo de leerlas todas, cruzarlas con el movimiento real de precio, y decidir qué amerita atención. MarketMind AI hace ese primer filtro con dos agentes de inteligencia artificial — y nunca ejecuta operaciones, siempre deja la decisión final a un humano."

---

## Persona 2 — Arquitectura + antialucinación + News Radar (0:35 – 1:15)

**[PANTALLA: News Radar → aplicar un filtro → mostrar una tarjeta de noticia con fuente y fecha]**

> "Nuestra arquitectura tiene dos agentes encadenados con **LangGraph**: el **Analista de Coyuntura de Mercados**, que lee una noticia y el precio real del instrumento afectado, y el **Asesor Financiero**, que arma el briefing final.
>
> Para evitar que la IA invente datos, el Analista solo puede usar la noticia y el precio que le damos — nunca información externa — y cada señal sale con evidencia citada y un disclaimer.
>
> Todo arranca en **News Radar**, donde filtramos noticias por instrumento, sector o antigüedad, siempre con fuente y fecha visibles."

---

## Persona 3 — Demo AI Analysis + Executive Briefing (1:15 – 2:05)

**[PANTALLA: AI Analysis generando una señal en vivo → Executive Briefing generando un briefing → panel de Tareas]**

> "Al generar el análisis, el Analista clasifica el impacto — positivo, negativo, neutral o incierto — con un nivel de confianza, evidencia concreta, y compara el evento contra el movimiento real de precio.
>
> Un humano siempre puede agregar su propia observación y marcar la señal como **revisada**, **escalada** o **descartada** — queda registrado quién decidió qué.
>
> Después, en **Executive Briefing**, el Asesor toma esa señal y genera una acción de investigación y una tarea de seguimiento — nunca una orden de compra o venta. Las tareas se pueden marcar como hechas, reabrir, o volver a ver el análisis completo con un clic."

---

## Persona 4 — Diferenciadores y cierre (2:05 – 2:50)

**[PANTALLA: Dashboard con el KPI de "track record" → Active Watchlist con ECU2035 → badge de modo LLM en la esquina]**

> "Más allá del mínimo del track, sumamos contexto real de Ecuador y LatAm con el bono soberano **ECU2035**, un dashboard con métricas reales — incluido un **track record** que audita si la clasificación del agente coincide con el movimiento real de precio — y toda la información persiste en una base de datos en la nube, no se pierde entre sesiones.
>
> La capa de IA es agnóstica de proveedor: hoy corre con Gemini, pero cambiar a Claude o DeepSeek es solo una variable de entorno. Y todo esto está respaldado por más de 30 tests automatizados que corren en cada cambio de código."

---

## Cierre — Todos o Persona 1 (2:50 – 3:00)

**[PANTALLA: vuelta al Dashboard]**

> "MarketMind AI es un asistente de investigación, no un robot que opera solo — así se ve un producto real de inteligencia de mercado, listo para integrarse al flujo de trabajo de un analista o una mesa de research. Gracias."

---

## Notas para grabar

- Cambia de pantalla **un par de segundos antes** de que la persona correspondiente empiece a hablar, para que no se vea el salto en seco.
- Si algo tarda en cargar (ej. Gemini real tarda unos segundos), ten una señal ya generada de respaldo para no perder tiempo en pantalla esperando.
- El orden de las pantallas sigue el recorrido real de la app: Dashboard → News Radar → AI Analysis → Executive Briefing → Dashboard/Watchlist. Si quieres el detalle de qué significa cada parte antes de grabar, está en [`RECORRIDO_APP.md`](RECORRIDO_APP.md).
- Total aproximado: ~420 palabras de guion. Si al ensayar se pasa de 3 minutos, lo primero que se puede recortar sin perder lo esencial es el párrafo de diferenciadores de la Persona 4 (Ecuador/LatAm y multi-proveedor pueden ir en una sola frase corta).
