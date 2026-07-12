# Checklist de entrega — Hackathon Agentic Scale (Track 5)

Basado en `DOCS/AgenticScale Entregable.pdf` y `DOCS/Formato de Entregables.docx` (comunicado de TAWS). **Fecha límite: domingo 12 de julio de 2026, 23:59 (Ecuador).** Tras el cierre solo se permiten correcciones menores de bugs, no funcionalidades nuevas.

## 1. Los 5 entregables obligatorios

Falta uno solo = penalización o posible descalificación de la preselección.

- [ ] **Video** (≤ 3 min, YouTube o nube) — grabado con [`GUION_VIDEO.md`](GUION_VIDEO.md) (4 personas) o [`GUION_DEMO.md`](GUION_DEMO.md) (1 persona, respaldo).
- [ ] **ZIP del código** — el repo completo, sin `node_modules/`, `.venv/`, `dist/` ni `.env` con claves reales.
- [ ] **Documento técnico** — [`DOCUMENTO_TECNICO.md`](DOCUMENTO_TECNICO.md) (ya incluye diagrama de arquitectura, track asignado, tipo de negocio e integración empresarial).
- [ ] **Link del repositorio** — debe quedar **público** y accesible durante toda la evaluación.
- [ ] **Link de despliegue** — demo funcionando en vivo:
  - Frontend: https://marketmind-ai-three.vercel.app
  - Backend (Swagger): https://track5-backend.onrender.com/docs

## 2. Formato exacto del correo de entrega

Enviar a **taws@fiec.espol.edu.ec**, asunto exacto **`Entrega Hackathon`** (sin variaciones). No borrar las etiquetas aunque alguna línea quede vacía.

```
Asunto: Entrega Hackathon

Nombre del equipo:
Link video:
Link ZIP código:
Link documento:
Link repositorio:
Link despliegue:
```

Si video, ZIP y documento están en una sola carpeta compartida (Drive/OneDrive), se puede pegar el mismo link en esas 3 líneas.

## 3. Antes de enviar — última pasada

- [ ] Recorrer la web en vivo (no localhost) siguiendo [`RECORRIDO_APP.md`](RECORRIDO_APP.md): Dashboard → News Radar → AI Analysis → Briefings → Watchlist.
- [ ] `pytest` en verde localmente (34 tests) y el badge de CI en verde en GitHub.
- [ ] Confirmar que el repo es público (probar el link en una ventana de incógnito).
- [ ] Confirmar que `DOCUMENTO_TECNICO.md` menciona el uso de Gemini (para calificar a "Best Use of Google Gemini").
- [ ] Si sobra tiempo: solo los 10 mejores equipos avanzan a la final presencial del **18 de julio en la Biblioteca ESPOL, Edificio 7A** — no es parte de esta entrega, pero conviene tenerlo en el radar.
