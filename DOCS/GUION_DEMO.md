# Guión de demo (video de 3 minutos)

Mapea cada criterio de aceptación del PDF del track a un clic concreto en la app. Pensado para grabar directo, sin cortes. **El hilo conductor es el caso Ecuador:** una noticia regulatoria local (Superintendencia de Bancos) impactando el bono soberano ECU2035 — el mismo pipeline de HU1→HU3, aplicado al mercado que más le importa a este jurado.

## 0. Intro (15s)

"¿Qué pasa con el bono soberano ecuatoriano cuando la Superintendencia de Bancos exige más liquidez a los bancos? Somos [equipo], Track 5, y construimos dos agentes IA — un Analista de Coyuntura y un Asesor Financiero — que responden eso en segundos con señales explicables, sin ejecutar operaciones."
(Mostrar el Dashboard un segundo.)

## 1. HU1 — Radar de noticias y activos (40s)

1. Ir a **News Radar**.
2. Señalar que cada card muestra **fuente** y **fecha/antigüedad** — y que conviven fuentes internacionales (Reuters, Bloomberg, CNBC, CoinDesk...) con **fuentes locales: Banco Central del Ecuador y Primicias** (≥2 fuentes ✓).
3. Usar los filtros: **Date Range** → Last 7d (el feed completo se reduce de forma visible), luego **Asset** → ECU2035 (quedan solo las noticias del bono soberano: Superintendencia de Bancos, BCE, FMI, remesas).
4. Señalar los **instrumentos** ligados en los chips (ECU2035, y en otras cards TSLA, NVDA, BTC...).
   > Cubre: "muestra noticias de ≥2 fuentes con fuente y fecha, relaciona cada noticia con instrumentos, permite filtrar por tipo/activo/antigüedad."

## 2. HU2 — Señal explicable de impacto (55s)

1. Desde la card **"Superintendencia de Bancos exige mayor colchon de liquidez a bancos medianos"** (Primicias), clic en **"Ver análisis"**.
2. Se genera la señal en vivo sobre **ECU2035**: mostrar el **badge de impacto** y el anillo de **confianza**.
3. Señalar la sección **Evidencia** (cita la noticia del regulador + el movimiento real de precio del bono en la ventana del evento).
4. Señalar la **comparación de precio** (ECU2035 pasó de X a Y) con su sparkline.
5. Señalar el **disclaimer** ("no constituye asesoría financiera personalizada y no garantiza resultados").
6. Mencionar que la acción sugerida es de **investigación**, nunca una orden de compra/venta.
   > Cubre: "clasifica impacto + confianza, compara contra movimiento de precio, explica con evidencia y fuentes, aclara que no es asesoría."

## 3. HU3 — Briefing con revisión humana (55s)

1. Ir a **Briefings** — la watchlist **Ecuador & LatAm** ya viene seleccionada — clic en **"Generar briefing"**.
2. Mostrar el item generado: noticia + movimiento + **acción de investigación sugerida** + resumen ejecutivo en bullets.
3. En la señal, escribir una observación en **"Observaciones del analista"** (ej. "cruzar con el informe de estabilidad de la Superintendencia"), cambiar el estado a **"escalada"** y **Guardar**.
4. Recargar la página (F5) y volver a pulsar **"Generar briefing"** — es instantáneo porque **reusa la señal persistida** — y mostrar que el estado y la justificación siguen ahí (centrarse en estado + justificación; los bullets del resumen pueden variar al reusar). También se ve en la lista "Señales generadas" de AI Analysis.
5. Señalar el panel de **Tareas/Alertas** a la derecha — remarcar en voz alta: **"nunca se genera una orden de compra o venta, solo tareas para que un humano decida."**
   > Cubre: "resumen por watchlist con noticia+movimiento+acción, marcar revisada/escalada/descartada guardando justificación, no ejecuta compras/ventas — crea alertas/tareas."

## 4. Cierre (15s)

"Los dos agentes están orquestados con **LangGraph** y el grafo decide: si una señal es neutral y de baja confianza, **ni siquiera gasta la llamada del Asesor** — la deja en monitoreo. Gemini como motor principal, swap de proveedor con una variable de entorno, y más de 35 tests — incluyendo el ruteo del grafo y que el sistema nunca sugiere ejecutar una operación." Mostrar brevemente `tests/` corriendo en verde o el link de despliegue.

## Notas de grabación

- Usar la URL de **despliegue en vivo** (no localhost) para que el jurado vea que el entregable #5 funciona.
- **Desplegar esta rama antes de grabar** (merge + push) y confirmar en la URL de producción que Briefings abre con **Ecuador & LatAm** preseleccionada — la preselección y el orden de noticias de este guion no existen en el deploy anterior.
- **Pre-generar** la señal de la Superintendencia y el briefing de Ecuador & LatAm antes de grabar (y de la ventana de evaluación): las llamadas sin `force` reusan lo persistido y responden al instante — sin riesgo de latencia ni de cuota de Gemini en cámara.
- Si Gemini tarda unos segundos en una generación en vivo, narrar durante la espera ("el Analista está leyendo la noticia y comparándola con el histórico del bono...").
- Calentar el backend (abrir `/api/health`) ~2 min antes de grabar por el cold start de Render.
