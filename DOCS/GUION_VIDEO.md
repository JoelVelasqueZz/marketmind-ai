# Guion de video — MarketMind AI (Track 5)

Guion para 4 personas, ~3 minutos totales. Cada bloque trae el texto exacto para leer y qué mostrar en pantalla al mismo tiempo (grabado con OBS sobre **https://marketmind-ai-three.vercel.app**). **El caso Ecuador (Superintendencia de Bancos → bono ECU2035) es el hilo conductor de toda la demo.** Los tiempos son aproximados a un ritmo de habla normal (~140 palabras/min) — ensayar una vez con cronómetro antes de grabar en serio.

---

## Persona 1 — Intro con el caso Ecuador (0:00 – 0:30)

**[PANTALLA: Dashboard, recién cargado]**

> "¿Qué le pasa al bono soberano ecuatoriano cuando la Superintendencia de Bancos exige más liquidez al sistema financiero? Un analista tarda horas en responderlo. Somos [nombre del equipo] y esto es **MarketMind AI**, nuestro proyecto para el **Track 5**: dos agentes de IA que convierten noticias en señales explicables y briefings para revisión humana — y que **nunca ejecutan operaciones**: la decisión final siempre es de una persona."

---

## Persona 2 — Arquitectura + antialucinación + News Radar (0:30 – 1:10)

**[PANTALLA: News Radar → filtrar Asset → ECU2035 → mostrar la card de la Superintendencia de Bancos con fuente y fecha]**

> "La arquitectura son dos agentes orquestados con **LangGraph**: el **Analista de Coyuntura**, que cruza cada noticia con el precio real del instrumento, y el **Asesor Financiero**, que arma el briefing. Y el grafo decide de verdad: si una señal es neutral y de baja confianza, **ni siquiera gasta la llamada del Asesor** — queda en monitoreo.
>
> Para evitar que la IA invente datos, el Analista solo puede usar la noticia y el precio que le damos, y cada señal sale con evidencia citada y disclaimer.
>
> En **News Radar** conviven Reuters o Bloomberg con fuentes locales — **Banco Central del Ecuador y Primicias** — con filtros por instrumento, tipo y antigüedad."

---

## Persona 3 — Demo: señal Superintendencia → ECU2035 + Briefing (1:10 – 2:05)

**[PANTALLA: clic en "Ver análisis" de la noticia de la Superintendencia → señal sobre ECU2035 → Briefings con Ecuador & LatAm → panel de Tareas]**

> "Tomamos la noticia real del regulador: la Superintendencia de Bancos exige más liquidez a los bancos. El Analista clasifica el impacto sobre el bono **ECU2035** con su nivel de confianza, evidencia concreta, y lo compara contra el movimiento real de precio del bono.
>
> El humano decide: agrega su observación y marca la señal como **revisada**, **escalada** o **descartada** — la decisión queda registrada con su justificación y fecha, y persiste en la base de datos.
>
> En **Briefings**, el Asesor convierte esa señal en una acción de investigación y una tarea de seguimiento — **nunca una orden de compra o venta**."

---

## Persona 4 — Diferenciadores y cierre (2:05 – 2:45)

**[PANTALLA: Dashboard con el KPI de "track record" → badge de modo LLM en la esquina]**

> "Todo esto no es solo para Ecuador: el mismo pipeline cubre acciones, cripto y crédito global. Sumamos un **track record** que audita si la clasificación del agente coincide con el movimiento real de precio, persistencia en la nube, y una capa de IA agnóstica: hoy corre con **Gemini**, cambiar a otro proveedor es una variable de entorno. Y hay más de **35 tests automatizados** — incluido el ruteo condicional del grafo — corriendo en cada cambio de código."

---

## Cierre — Todos o Persona 1 (2:45 – 2:55)

**[PANTALLA: vuelta al Dashboard]**

> "MarketMind AI es un asistente de investigación, no un robot que opera solo — inteligencia de mercado explicable, hecha pensando en el mercado ecuatoriano. Gracias."

---

## Notas para grabar

- Cambia de pantalla **un par de segundos antes** de que la persona correspondiente empiece a hablar, para que no se vea el salto en seco.
- **Desplegar esta rama antes de grabar** (merge + push) y confirmar en la URL de producción que Briefings abre con **Ecuador & LatAm** preseleccionada.
- **Pre-generar antes de grabar** la señal de la noticia de la Superintendencia y el briefing de Ecuador & LatAm (se reusan al instante y no dependen de la cuota de Gemini en cámara). Calentar el backend abriendo `/api/health` ~2 min antes.
- El orden de las pantallas sigue el recorrido real de la app: Dashboard → News Radar (ECU2035) → AI Analysis (Superintendencia) → Briefings (Ecuador & LatAm) → Dashboard. El detalle página por página está en [`RECORRIDO_APP.md`](RECORRIDO_APP.md).
- Total ~370 palabras de guion. Si al ensayar se pasa de 3 minutos, recortar primero la primera frase de la Persona 4 ("Todo esto no es solo para Ecuador...").
