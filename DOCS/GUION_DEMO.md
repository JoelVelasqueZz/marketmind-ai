# Guión de demo (video de 3 minutos) — versión 1 narrador

> Este es el guión de respaldo para un solo narrador. El guión oficial para grabar con 4 personas es [`GUION_VIDEO.md`](GUION_VIDEO.md) — usa este solo si al final graba una sola persona.

Mapea cada criterio de aceptación del PDF del track a un clic concreto en la app. Pensado para grabar directo, sin cortes.

## 0. Intro (15s)
"Somos [equipo], Track 5. Construimos dos agentes IA — un Analista de Coyuntura de Mercados y un Asesor Financiero — que convierten noticias en señales explicables y briefings para revisión humana, sin ejecutar operaciones."
(Mostrar el Dashboard un segundo.)

## 1. HU1 — Radar de noticias y activos (40s)

1. Ir a **News Radar**.
2. Señalar que cada card muestra **fuente** (Reuters, Bloomberg, CNBC, CoinDesk, FT, WSJ — ≥2 fuentes) y **fecha/antigüedad** ("12m ago", "2d ago"...).
3. Señalar los **instrumentos** ligados (chips: TSLA, NVDA, BTC...).
4. Usar los filtros: **Asset Type** → Crypto (mostrar que solo quedan noticias de cripto), **Date Range** → Last 24h (mostrar que se reduce el feed), **Asset** → NVDA.
   > Cubre: "muestra noticias de ≥2 fuentes con fuente y fecha, relaciona cada noticia con instrumentos, permite filtrar por tipo/activo/antigüedad."

## 2. HU2 — Señal explicable de impacto (55s)

1. Desde una card de noticia (ej. la de NVIDIA / chip export restrictions), clic en **"Ver análisis"**.
2. Se genera la señal en vivo: mostrar el badge **Negative**, el anillo de **confianza** (95%).
3. Señalar la sección **Evidencia** (cita la noticia + el movimiento real de precio, -9.4% en la ventana).
4. Señalar la **comparación de precio** (NVDA pasó de X a Y).
5. Señalar el **disclaimer** ("no constituye asesoría personalizada ni garantiza resultados").
6. Mencionar que la acción sugerida es de **investigación**, nunca una orden de compra/venta.
   > Cubre: "clasifica impacto + confianza, compara contra movimiento de precio, explica con evidencia y fuentes, aclara que no es asesoría."

## 3. HU3 — Briefing con revisión humana (55s)

1. Ir a **Briefings**, seleccionar la watchlist **Tech Megacaps**, clic en **"Generar briefing"**.
2. Mostrar los items generados: noticia + movimiento + **acción de investigación sugerida** + resumen ejecutivo en bullets.
3. En una señal, escribir una observación en **"Observaciones del analista"**, cambiar el estado a **"revisada"** (o "escalada"/"descartada") y **Guardar**.
4. Recargar la página (F5) y mostrar que el estado y la justificación **persisten**.
5. Señalar el panel de **Tareas/Alertas** a la derecha — remarcar en voz alta: **"nunca se genera una orden de compra o venta, solo tareas para que un humano decida."**
   > Cubre: "resumen por watchlist con noticia+movimiento+acción, marcar revisada/escalada/descartada guardando justificación, no ejecuta compras/ventas — crea alertas/tareas."

## 4. Cierre (15s)

"Los dos agentes están orquestados con LangGraph, con Gemini como motor principal — swap de proveedor con una variable de entorno — y toda la arquitectura queda documentada en el repo, incluyendo tests que verifican que el sistema nunca sugiere ejecutar una operación." Mostrar brevemente `tests/` corriendo en verde o el link de despliegue en el navegador.

## Notas de grabación
- Usar la URL de **despliegue en vivo** (no localhost) para que el jurado vea que el entregable #5 funciona.
- Si el LLM está en `MODE=mock`, el análisis sigue siendo coherente (reglas deterministas basadas en la noticia + el precio real) — no hace falta esperar latencia de red si no hay tiempo, pero si hay `GOOGLE_API_KEY` configurada, mejor mostrar Gemini real al menos una vez para calificar al premio "Best Use of Google Gemini".
