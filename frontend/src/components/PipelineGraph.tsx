import type { TraceRun } from "../types";

interface PipelineGraphProps {
  run: TraceRun;
}

// Grafo fijo del pipeline (SVG a mano, sin librerías): el layout no cambia,
// solo se resalta el camino que ESTA corrida recorrió según sus eventos.
export default function PipelineGraph({ run }: PipelineGraphProps) {
  const visited = new Set<string>();
  let edgeTarget: string | null = null;
  for (const e of run.events) {
    if (e.type === "node_start" && e.node) visited.add(e.node);
    if (e.type === "reuse") visited.add("reuse");
    if (e.type === "edge_decision" && e.target) edgeTarget = e.target;
  }
  const isReuse = run.path === "briefing-reuse";
  const entryLabel = isReuse ? "Señal reusada" : "Analista";
  const entryVisited = isReuse ? visited.has("reuse") : visited.has("analyst");
  const decisionEvent = run.events.find((e) => e.type === "edge_decision");

  const nodeClass = (active: boolean) =>
    active
      ? "fill-primary-container stroke-primary"
      : "fill-surface-container-low stroke-outline-variant opacity-40";
  const textClass = (active: boolean) =>
    active ? "fill-on-primary-container font-bold" : "fill-on-surface-variant opacity-50";
  const edgeClass = (active: boolean) =>
    active ? "stroke-primary" : "stroke-outline-variant opacity-30";

  const toAdvisor = edgeTarget === "advisor";
  const toMonitor = edgeTarget === "monitor";

  return (
    <svg viewBox="0 0 400 150" className="w-full" role="img" aria-label="Camino de ejecución del pipeline">
      {/* Entrada -> decisión */}
      <line x1="118" y1="75" x2="176" y2="75" strokeWidth="2" className={edgeClass(decisionEvent != null)} />
      {/* decisión -> Asesor (arriba) */}
      <line x1="212" y1="62" x2="286" y2="34" strokeWidth="2" className={edgeClass(toAdvisor)} />
      {/* decisión -> Monitor (abajo) */}
      <line x1="212" y1="88" x2="286" y2="116" strokeWidth="2" className={edgeClass(toMonitor)} />

      {/* Nodo de entrada (Analista o Reuso) */}
      <rect x="10" y="55" width="108" height="40" rx="10" strokeWidth="1.5" className={nodeClass(entryVisited)} />
      <text x="64" y="79" textAnchor="middle" fontSize="12" className={textClass(entryVisited)}>
        {entryLabel}
      </text>

      {/* Rombo de decisión */}
      <polygon
        points="194,55 216,75 194,95 172,75"
        strokeWidth="1.5"
        className={nodeClass(decisionEvent != null)}
      />
      <text x="194" y="79" textAnchor="middle" fontSize="10" className={textClass(decisionEvent != null)}>
        &lt;0.5?
      </text>

      {/* Asesor */}
      <rect x="288" y="12" width="102" height="40" rx="10" strokeWidth="1.5" className={nodeClass(visited.has("advisor"))} />
      <text x="339" y="36" textAnchor="middle" fontSize="12" className={textClass(visited.has("advisor"))}>
        Asesor
      </text>

      {/* Monitor */}
      <rect x="288" y="98" width="102" height="40" rx="10" strokeWidth="1.5" className={nodeClass(visited.has("monitor"))} />
      <text x="339" y="122" textAnchor="middle" fontSize="12" className={textClass(visited.has("monitor"))}>
        Monitoreo · $0
      </text>

      {/* Etiqueta de la decisión tomada */}
      {decisionEvent?.inputs && (
        <text x="194" y="112" textAnchor="middle" fontSize="9" className="fill-on-surface-variant">
          {decisionEvent.inputs.impact} · {Math.round(decisionEvent.inputs.confidence * 100)}%
        </text>
      )}
      {!decisionEvent && !isReuse && (
        <text x="200" y="145" textAnchor="middle" fontSize="9" className="fill-on-surface-variant">
          HU2: solo el Analista corre; el ruteo ocurre al generar el briefing
        </text>
      )}
    </svg>
  );
}
