import { useEffect, useState } from "react";
import { api } from "../api";
import ImpactBadge from "./ImpactBadge";
import PipelineGraph from "./PipelineGraph";
import { formatConfidence } from "../lib/format";
import type {
  Attribution,
  Compliance,
  ReviewEvent,
  Signal,
  TraceDoc,
  TraceEvent,
  TraceRun,
} from "../types";

interface TraceDrawerProps {
  signal: Signal;
  onClose: () => void;
}

type TabId = "cumplimiento" | "maquina" | "humana";

const PATH_LABEL: Record<TraceRun["path"], string> = {
  analysis: "Generación directa",
  briefing: "Pipeline del briefing",
  "briefing-reuse": "Reuso en briefing",
};

const NODE_LABEL: Record<string, string> = {
  analyst: "el Analista",
  advisor: "el Asesor",
  monitor: "Monitoreo",
};

// Nombres llanos de los checks del Compliance Gate (jerga → humano).
const CHECK_LABEL: Record<string, string> = {
  impacto_en_taxonomia: "Impacto dentro de las 4 categorías válidas",
  confianza_en_rango: "Confianza dentro de un rango válido",
  evidencia_suficiente: "Evidencia suficiente (2 a 4 puntos)",
  cifras_ancladas_al_dato: "Cifras verificadas contra el dato de mercado",
  fuente_verificada: "Fuentes reales de la noticia (no inventadas)",
  accion_no_es_orden: "La acción nunca es una orden de compra/venta",
};

const CAUSE_LABEL: Record<string, string> = {
  evidencia_insuficiente: "evidencia insuficiente",
  sobre_reaccion_al_precio: "sobre-reacción al precio",
  dato_no_soportado_por_fuente: "dato no soportado por la fuente",
  contexto_faltante: "contexto faltante",
  criterio_del_comite: "criterio del Comité",
};

function prettify(item: string): string {
  return CHECK_LABEL[item] ?? item.replace(/_/g, " ");
}

function providerLabel(llmMode: string, model: string): string {
  return llmMode === "mock" ? "mock · determinista (sin LLM)" : `${llmMode} · ${model}`;
}

function fmtUsd(value: number): string {
  if (value === 0) return "$0";
  return `$${value.toFixed(6).replace(/0+$/, "").replace(/\.$/, "")}`;
}

function runCostSummary(run: TraceRun): { cost: number; saved: number } {
  let cost = 0;
  let saved = 0;
  for (const e of run.events) {
    if (e.type === "llm_call" && typeof e.cost_usd === "number") cost += e.cost_usd;
    if (e.type === "edge_decision" && typeof e.saved_usd_est === "number") saved += e.saved_usd_est;
  }
  return { cost, saved };
}

// Cada evento crudo → una frase en lenguaje llano (+ un dato técnico gris opcional).
function eventLine(e: TraceEvent): { icon: string; text: string; sub?: string; highlight?: boolean } | null {
  const node = e.node ? NODE_LABEL[e.node] ?? e.node : "";
  switch (e.type) {
    case "node_start":
      return { icon: "play_circle", text: `Empieza ${node}` };
    case "node_end":
      return { icon: "check_circle", text: `Termina ${node}` };
    case "llm_call":
      return {
        icon: "smart_toy",
        text: `La IA redactó el análisis · ${typeof e.cost_usd === "number" ? fmtUsd(e.cost_usd) : "—"}`,
        sub:
          e.tokens_in != null
            ? `${e.tokens_in}→${e.tokens_out} tokens · ${e.latency_ms} ms · intento ${e.attempts} (${e.measured ? "medido" : "estimado"})`
            : `${e.latency_ms} ms · intento ${e.attempts}`,
      };
    case "edge_decision": {
      const conf = e.inputs ? Math.round(e.inputs.confidence * 100) : 0;
      const toMonitor = e.target === "monitor";
      return {
        icon: "alt_route",
        text: toMonitor
          ? `La confianza (${conf}%) bajó del 50%: el sistema NO gastó en el Asesor, fue a Monitoreo ($0)`
          : `La confianza (${conf}%) superó el umbral: pasa al Asesor`,
        sub:
          toMonitor && typeof e.saved_usd_est === "number" && e.saved_usd_est > 0
            ? `ahorró ≈ ${fmtUsd(e.saved_usd_est)}`
            : undefined,
        highlight: true,
      };
    }
    case "reuse":
      return { icon: "cached", text: "Señal reusada — el Analista no vuelve a correr" };
    case "guardrail":
      return { icon: "shield", text: "Un guardrail reemplazó lenguaje de orden por una acción de revisión", highlight: true };
    case "retry":
      return {
        icon: "restart_alt",
        text: "El control rechazó el primer borrador: una cifra no cuadraba · la IA la corrigió sola",
        sub: `intento ${e.attempt}`,
        highlight: true,
      };
    case "gate":
      return {
        icon: "verified",
        text:
          e.verdict === "corregida"
            ? `Tras la corrección, pasó las ${e.total} revisiones`
            : `Pasó las ${e.total} revisiones de cumplimiento`,
        highlight: true,
      };
    default:
      return null; // contrato v1: tipos desconocidos se ignoran
  }
}

function VerdictLine({ compliance }: { compliance: Compliance }) {
  const map = {
    ok: {
      cls: "bg-success/15 text-success border-success/30",
      icon: "verified",
      text: `Despachada · pasó los ${compliance.total} controles a la primera`,
    },
    corregida: {
      cls: "bg-warning/15 text-warning border-warning/30",
      icon: "auto_fix_high",
      text: "La IA se pasó de la raya en un borrador · el control lo atrapó y lo corrigió solo",
    },
    marcada: {
      cls: "bg-error-container/20 text-error border-error/40",
      icon: "gpp_maybe",
      text: "Marcada · un control la detuvo para revisión humana",
    },
  }[compliance.verdict];
  return (
    <div className={`flex items-center gap-2 rounded-lg border p-2.5 mb-3 ${map.cls}`}>
      <span className="material-symbols-outlined text-lg">{map.icon}</span>
      <span className="text-body-md font-bold">{map.text}</span>
    </div>
  );
}

function MachineCard({ run }: { run: TraceRun }) {
  const { cost, saved } = runCostSummary(run);
  return (
    <div className="flex-1 bg-surface-container-low border border-outline-variant rounded-xl p-3">
      <div className="flex items-center gap-1.5 mb-1">
        <span className="material-symbols-outlined text-sm text-on-surface-variant">memory</span>
        <span className="text-label-sm font-bold text-on-surface">Lo registró la máquina</span>
      </div>
      <p className="text-label-sm text-on-surface-variant mb-2">reglas y datos, no los inventó la IA</p>
      <p className="text-label-sm text-on-surface-variant">Costo de esta señal</p>
      <p className="font-mono-data text-headline-md text-on-surface font-bold">{fmtUsd(cost)}</p>
      {saved > 0 && (
        <span className="inline-block mt-1 px-2 py-0.5 bg-primary-container/20 text-primary text-[11px] font-bold rounded-full">
          Ahorró ≈ {fmtUsd(saved)} al no escalar
        </span>
      )}
      <p className="text-label-sm text-on-surface-variant mt-2">{providerLabel(run.llm_mode, run.model)}</p>
    </div>
  );
}

function ModelCard({ signal, reasoning }: { signal: Signal; reasoning?: string | null }) {
  return (
    <div className="flex-1 bg-primary-container/10 border border-primary/40 rounded-xl p-3">
      <div className="flex items-center gap-1.5 mb-1">
        <span className="material-symbols-outlined text-sm text-primary">smart_toy</span>
        <span className="text-label-sm font-bold text-primary">Lo declaró la IA</span>
      </div>
      <p className="text-label-sm text-on-surface-variant mb-2">lo revisa una persona</p>
      <div className="flex items-center gap-2 mb-1">
        <ImpactBadge impact={signal.impact} />
        <span className="font-mono-data text-mono-data text-on-surface">
          {formatConfidence(signal.confidence)}
        </span>
      </div>
      {reasoning && (
        <p className="text-label-sm text-on-surface-variant italic line-clamp-2">“{reasoning}”</p>
      )}
    </div>
  );
}

export default function TraceDrawer({ signal, onClose }: TraceDrawerProps) {
  const [trace, setTrace] = useState<TraceDoc | null>(null);
  const [runIndex, setRunIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [attribution, setAttribution] = useState<Attribution | null>(null);
  const [attribLoading, setAttribLoading] = useState(false);
  const [attribError, setAttribError] = useState<string | null>(null);
  const [replayIndex, setReplayIndex] = useState<number | null>(null);
  const [events, setEvents] = useState<ReviewEvent[]>([]);
  const [activeTab, setActiveTab] = useState<TabId>(signal.compliance ? "cumplimiento" : "maquina");

  useEffect(() => {
    api
      .getSignalTrace(signal.id)
      .then((t) => {
        setTrace(t);
        setRunIndex(t.runs.length - 1);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
    api.getSignalEvents(signal.id).then(setEvents).catch(() => setEvents([]));
  }, [signal.id]);

  useEffect(() => {
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  const run = trace?.runs[runIndex];

  // Replay animado: revela los eventos uno a uno con su timing real (comprimido).
  useEffect(() => {
    if (run == null || replayIndex == null) return;
    if (replayIndex >= run.events.length - 1) return;
    const cur = run.events[replayIndex];
    const next = run.events[replayIndex + 1];
    const delay = Math.min(800, Math.max(250, (next?.t_ms ?? 0) - (cur?.t_ms ?? 0)));
    const timer = setTimeout(() => setReplayIndex((i) => (i == null ? i : i + 1)), delay);
    return () => clearTimeout(timer);
  }, [run, replayIndex]);

  async function loadAttribution() {
    setAttribLoading(true);
    setAttribError(null);
    try {
      setAttribution(await api.computeAttribution(signal.id));
    } catch (err) {
      setAttribError(err instanceof Error ? err.message : String(err));
    } finally {
      setAttribLoading(false);
    }
  }

  const visibleEvents =
    run == null ? [] : replayIndex == null ? run.events : run.events.slice(0, replayIndex + 1);
  const visibleRun = run == null ? null : { ...run, events: visibleEvents };
  const compliance = signal.compliance;
  const checksSorted = compliance
    ? [...compliance.checks].sort((a, b) => Number(a.passed) - Number(b.passed))
    : [];

  const TABS: { id: TabId; label: string }[] = [
    ...(compliance ? [{ id: "cumplimiento" as TabId, label: `Cumplimiento · ${compliance.passed}/${compliance.total}` }] : []),
    { id: "maquina", label: "Sala de Máquinas" },
    { id: "humana", label: `Revisión humana${events.length ? ` · ${events.length}` : ""}` },
  ];

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-[60]" onClick={onClose} />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Caja de Cristal: expediente de ejecución"
        className="fixed inset-y-0 right-0 w-full max-w-[440px] bg-surface-container border-l border-outline-variant z-[70] overflow-y-auto p-5"
      >
        {/* Header + tesis */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-headline-md text-headline-md text-on-surface font-bold">
              Caja de Cristal
            </h3>
            <p className="text-label-sm text-on-surface-variant max-w-[300px]">
              La ejecución real del orquestador, no una explicación del propio modelo.
            </p>
            <span
              className="inline-block mt-1 px-2 py-0.5 bg-surface-variant text-on-surface-variant text-[11px] font-bold rounded-full"
              title={`señal ${signal.id}`}
            >
              {signal.instrument}
            </span>
          </div>
          <button
            className="material-symbols-outlined text-on-surface-variant hover:text-on-surface"
            onClick={onClose}
            aria-label="Cerrar"
          >
            close
          </button>
        </div>

        {error && <p className="text-body-md text-error mb-4">{error}</p>}

        {trace && trace.runs.length > 1 && (
          <div className="flex gap-1.5 mb-3">
            {trace.runs.map((r, i) => (
              <button
                key={i}
                onClick={() => {
                  setRunIndex(i);
                  setReplayIndex(null);
                }}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-bold border ${
                  i === runIndex
                    ? "bg-primary-container text-on-primary-container border-primary"
                    : "bg-surface-container-low text-on-surface-variant border-outline-variant"
                }`}
              >
                {PATH_LABEL[r.path]}
              </button>
            ))}
          </div>
        )}

        {visibleRun && run && (
          <>
            {/* HÉROE: veredicto + dualidad + grafo (siempre visible) */}
            {compliance && <VerdictLine compliance={compliance} />}

            <div className="flex gap-3 mb-3">
              <MachineCard run={run} />
              <ModelCard signal={signal} reasoning={run.reasoning} />
            </div>

            <div className="relative bg-surface-container-low border border-outline-variant rounded-xl p-3 mb-4">
              <PipelineGraph run={visibleRun} />
              <button
                className="absolute top-2 right-2 flex items-center justify-center w-8 h-8 bg-surface-container border border-outline-variant rounded-full text-primary hover:border-primary"
                title="Reproducir la ejecución paso a paso"
                aria-label="Reproducir la ejecución paso a paso"
                onClick={() => {
                  setReplayIndex(0);
                  setActiveTab("maquina");
                }}
              >
                <span className="material-symbols-outlined text-lg">
                  {replayIndex != null && replayIndex < run.events.length - 1 ? "pause_circle" : "smart_display"}
                </span>
              </button>
            </div>

            {/* Barra de pestañas (marco fijo) */}
            <div role="tablist" className="flex gap-1 mb-3 border-b border-outline-variant">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  role="tab"
                  aria-selected={activeTab === t.id}
                  onClick={() => setActiveTab(t.id)}
                  className={`px-3 py-2 text-label-sm font-bold border-b-2 -mb-px ${
                    activeTab === t.id
                      ? "border-primary text-primary"
                      : "border-transparent text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Pestaña: Cumplimiento */}
            {activeTab === "cumplimiento" && compliance && (
              <div role="tabpanel">
                <p className="text-label-sm text-on-surface-variant mb-2">
                  Controles de cumplimiento · {compliance.passed} de {compliance.total} aprobados
                  {compliance.verdict === "corregida" && " (1 autocorregido)"}
                </p>
                <ul className="space-y-2">
                  {checksSorted.map((c) => (
                    <li
                      key={c.item}
                      className="flex items-start gap-2 text-body-md text-on-surface-variant"
                      title={c.rule}
                    >
                      <span
                        className={`material-symbols-outlined text-sm mt-0.5 ${c.passed ? "text-success" : "text-error"}`}
                      >
                        {c.passed ? "check_circle" : "cancel"}
                      </span>
                      <span>
                        <b className="text-on-surface">{prettify(c.item)}</b>
                        <span className="block text-label-sm">{c.detail}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Pestaña: Sala de Máquinas */}
            {activeTab === "maquina" && (
              <div role="tabpanel">
                <p className="text-label-sm text-on-surface-variant mb-2">
                  {providerLabel(run.llm_mode, run.model)} ·{" "}
                  {new Date(run.started_at).toLocaleString("es-EC")}
                  {run.truncated && " · traza recortada"}
                </p>
                <ol className="space-y-2">
                  {visibleEvents.map((e, idx) => {
                    const line = eventLine(e);
                    if (!line) return null;
                    return (
                      <li
                        key={idx}
                        className={`flex items-start gap-2 text-body-md rounded-lg p-2 ${
                          line.highlight
                            ? "bg-primary-container/10 border border-primary/30 text-on-surface"
                            : "text-on-surface-variant"
                        }`}
                      >
                        <span className="material-symbols-outlined text-sm mt-0.5 text-primary">
                          {line.icon}
                        </span>
                        <span>
                          {line.text}
                          {line.sub && (
                            <span className="block text-label-sm text-on-surface-variant font-mono-data">
                              {line.sub}
                            </span>
                          )}
                        </span>
                      </li>
                    );
                  })}
                </ol>
              </div>
            )}

            {/* Pestaña: Revisión humana */}
            {activeTab === "humana" && (
              <div role="tabpanel" className="space-y-4">
                <div>
                  <p className="text-label-sm uppercase font-bold text-primary mb-1">
                    Lo declaró la IA (razonamiento)
                  </p>
                  <p className="text-body-md text-on-surface-variant italic">
                    {run.reasoning ? `“${run.reasoning}”` : "Sin razonamiento registrado."}
                  </p>
                </div>

                {events.length > 0 && (
                  <div>
                    <p className="text-label-sm uppercase font-bold text-primary mb-2">
                      Quién lo revisó · {events.length}
                    </p>
                    <ol className="space-y-2">
                      {events.map((ev, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-body-md text-on-surface-variant">
                          <span className="material-symbols-outlined text-sm mt-0.5 text-primary">person</span>
                          <span>
                            <b>{ev.reviewer}</b> ({ev.role}) · {ev.from_status} → <b>{ev.to_status}</b>
                            {ev.cause && ` · ${CAUSE_LABEL[ev.cause] ?? ev.cause}`}
                            <span className="block text-label-sm">
                              {new Date(ev.at).toLocaleString("es-EC")} — “{ev.justification}”
                            </span>
                          </span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-label-sm uppercase font-bold text-primary">¿Qué pesó más?</p>
                    {!attribution && (
                      <button
                        className="px-3 py-1.5 bg-primary-container text-on-primary-container text-label-sm font-bold rounded-lg disabled:opacity-40"
                        disabled={attribLoading}
                        onClick={loadAttribution}
                      >
                        {attribLoading ? "Sondeando…" : "Probar qué pasa si quito un dato"}
                      </button>
                    )}
                  </div>
                  {attribError && <p className="text-body-md text-error">{attribError}</p>}
                  {attribution && (
                    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-3 space-y-2">
                      <p className="text-body-md text-on-surface">
                        Señal original: <b>{attribution.base.impact}</b> ·{" "}
                        {formatConfidence(attribution.base.confidence)}
                      </p>
                      {attribution.probes.map((p) => (
                        <p key={p.key} className="text-body-md text-on-surface-variant">
                          <span className="material-symbols-outlined text-sm mr-1 align-middle">science</span>
                          {p.label}: <b>{p.impact}</b> · {formatConfidence(p.confidence)}
                          {p.impact !== attribution.base.impact && " — el impacto no se sostiene"}
                        </p>
                      ))}
                      {run.llm_mode !== attribution.llm_mode && (
                        <p className="text-label-sm text-error">
                          Sondeo con proveedor distinto al original ({attribution.llm_mode} vs {run.llm_mode}).
                        </p>
                      )}
                      <p className="text-label-sm text-on-surface-variant">{attribution.note}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </aside>
    </>
  );
}
