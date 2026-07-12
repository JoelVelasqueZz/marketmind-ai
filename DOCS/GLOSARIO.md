# Glosario — MarketMind AI (Track 5)

Explicación en lenguaje simple de los términos financieros y técnicos del proyecto, y de qué hace cada parte de la web. Pensado para quien no viene del mundo financiero ni de IA.

## 1. Conceptos financieros

**Instrumento** — cualquier cosa que se puede "seguir" en el mercado: una acción (AAPL), una criptomoneda (BTC), un bono (ECU2035), un par de divisas (EURUSD). En la app cada instrumento tiene un `symbol` (el código corto, ej. "NVDA") y un `type`:
- `equity` — acción de una empresa (Apple, Microsoft, NVIDIA, Tesla).
- `crypto` — criptoactivo (Bitcoin, Ethereum).
- `credit` — instrumento de renta fija / deuda (ETFs de bonos como HYG/TLT, o el bono soberano de Ecuador).
- `other` — todo lo demás (en nuestro caso, el par de divisas EUR/USD).

**Sector** — el rubro al que pertenece el instrumento (Tecnología, Semiconductores, Automotriz, Renta Fija, Macro/Ecuador, etc.). Sirve para agrupar y filtrar.

**Precio (`price`) y % de cambio (`change_pct`)** — cuánto vale el instrumento y cuánto subió o bajó en un período. Un `+` significa que subió, un `-` que bajó.

**Sparkline** — el mini-gráfico de líneas que se ve junto a cada activo (últimos 14 días de precio). Es solo para dar una idea visual rápida de la tendencia, no reemplaza un gráfico completo.

**Volatilidad** — qué tanto se mueve el precio de un activo. Si un activo sube y baja mucho en poco tiempo, es "volátil" (más riesgo/incertidumbre). En la página Watchlist calculamos una "volatilidad promedio" simple: el promedio de los cambios porcentuales absolutos de los activos de esa watchlist.

**Watchlist** — una "lista de seguimiento": un grupo de instrumentos que un analista quiere monitorear juntos (ej. "Tech Megacaps" = AAPL+MSFT+NVDA).

**Disclaimer** — el aviso legal/ético que aparece en cada señal: aclara que el contenido es informativo, no es asesoría financiera personalizada, y no garantiza resultados. Es obligatorio por las reglas del hackathon (el sistema nunca debe sonar como que te está diciendo "compra esto" con garantía de ganancia).

**Riesgo país / bono soberano** (contexto del instrumento ECU2035) — cuando un país emite deuda (bonos) en dólares para financiarse, el precio de esos bonos en el mercado secundario refleja qué tan riesgoso ven los inversionistas a ese país: si el precio del bono sube, significa que el riesgo percibido bajó (buena señal); si baja, el riesgo percibido subió (mala señal).

## 2. Conceptos de IA / agentes

**LLM (Large Language Model)** — el modelo de inteligencia artificial que genera texto (en este proyecto, Gemini de Google, o Claude como alterno). Es el "cerebro" que lee la noticia y redacta el análisis.

**Agente** — un programa que usa un LLM para cumplir una tarea específica de forma más o menos autónoma. Este proyecto tiene **dos agentes**:
- **Analista de Coyuntura de Mercados IA** — lee una noticia + el movimiento de precio del instrumento relacionado, y genera una **señal explicable** (impacto, confianza, evidencia).
- **Asesor Financiero e Inversiones IA** — toma esa señal y arma un **briefing** con una acción de investigación sugerida, para que un humano la revise.

**LangGraph / grafo de estados (StateGraph)** — la herramienta que usamos para **encadenar** los dos agentes (Analista → Asesor) de forma ordenada y testeable, en vez de simplemente llamar al LLM sueltas veces sin estructura. Cada agente es un "nodo" del grafo.

**Prompt** — las instrucciones de texto que le mandamos al LLM (qué debe hacer, qué reglas debe seguir, qué datos tiene disponibles).

**Salida estructurada (structured output)** — en vez de dejar que el LLM responda "como quiera", le exigimos que devuelva la respuesta en un formato exacto (ej. siempre con los campos `impact`, `confidence`, `evidence`...). Esto evita ambigüedad y hace la respuesta fácil de mostrar en la web.

**Modo mock (`LLM_MODE=mock`)** — un "modo de prueba" donde el sistema **no llama a ningún LLM real**: usa reglas de Python fijas (basadas en el % de cambio del precio) para simular una respuesta coherente. Sirve para desarrollar y demostrar sin gastar créditos ni depender de que la API esté disponible.

**Alucinación (hallucination)** — cuando un LLM "inventa" datos que no son ciertos (una cifra falsa, una fuente que no existe). Es el riesgo #1 a mitigar en un proyecto de IA financiera — por eso el Analista solo puede usar la noticia y el precio que le pasamos, nunca inventar información externa.

**API key** — la "clave" secreta que autoriza a nuestro backend a usar un servicio externo (en este caso, Gemini). Nunca debe subirse al repositorio público — vive en variables de entorno (`.env`, o configurada en el dashboard de Render).

**Reintentos con backoff (retry)** — cuando el LLM falla temporalmente (ej. "alta demanda"), el sistema reintenta automáticamente unas veces antes de rendirse, en vez de fallar de inmediato.

## 3. Qué hace cada parte de la web

**Dashboard** — pantalla de inicio, resumen general. Hoy son 3 tarjetas que llevan a las otras secciones (se puede mejorar con métricas reales, ver sección de mejoras).

**News Radar (HU1)** — el "feed" de noticias. Cada tarjeta muestra: fuente, cuánto tiempo hace se publicó, de qué instrumentos habla, y un botón "Ver análisis" que te lleva a generar la señal de esa noticia. Se puede filtrar por tipo de instrumento, activo específico o antigüedad, y buscar por texto libre desde la barra de arriba.

**AI Analysis (HU2)** — donde se genera y se ve la **señal explicable**: eliges un instrumento y una noticia, el sistema llama al Analista IA y te muestra impacto (positivo/negativo/neutral/incierto), % de confianza (el anillo circular), evidencia citada, comparación real de precio, y el disclaimer.

**Briefings (HU3)** — el resumen ejecutivo por watchlist. Aquí el Asesor IA arma, para cada instrumento de la lista, un mini-reporte con la noticia, el movimiento de precio y una **acción de investigación sugerida** (nunca una orden de compra/venta). Cada señal se puede marcar como **revisada**, **escalada** o **descartada**, con una justificación escrita — eso queda guardado permanentemente. A la derecha está el panel de **Tareas/Alertas**, que se pueden marcar como hechas.

**Watchlist** — vista de "mercado" tipo Google Finance/CoinMarketCap: tabla con precio, cambio del día, mini-gráfico (sparkline), y si ya se generó una señal para ese activo, su clasificación y confianza. No es un requisito mínimo del track, es un extra.

## 4. Estados de una señal (HU3)

- `pending` — recién generada, nadie la ha revisado todavía.
- `revisada` — un analista humano la vio y la validó.
- `escalada` — un analista humano decidió que necesita atención de alguien más (ej. un comité de riesgo).
- `descartada` — un analista humano decidió que no amerita seguimiento.

Ninguno de estos estados ejecuta ninguna acción automática de compra/venta — solo cambian cómo se ve la señal en la interfaz y quedan guardados con la justificación de quien la revisó.

## 5. Siglas del hackathon

- **HU** — Historia de Usuario (los "requisitos" del track, escritos como "Como [rol], quiero [algo], para que [beneficio]").
- **Track 5** — la categoría específica del hackathon que nos tocó: "Inteligencia de Mercado y Recomendaciones Informadas por Noticias".
- **SDD** — Spec-Driven Development, la metodología del taller: escribir primero qué debe pasar (specs verificables) antes de que la IA escriba código.
- **CI** — Integración Continua (Continuous Integration): que las pruebas automatizadas corran solas cada vez que se sube código nuevo (lo tenemos con GitHub Actions).
