import { useEffect, useState } from "react";
import { api } from "../api";
import PipelineGraph from "./PipelineGraph";
import { formatConfidence } from "../lib/format";
import type {
  Attribution,
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

const PATH_LABEL: Record<TraceRun["path"], string> = {
  analysis: "Generación directa (AI Analysis)",
  briefing: "Pipeline del briefing",
  "briefing-reuse": "Reuso en briefing",
};

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

function eventLine(e: TraceEvent): { icon: string; text: string; highlight?: boolean } | null {
  switch (e.type) {
    case "node_start":
      return { icon: "play_circle", text: `Nodo ${e.node} inicia` };
    case "node_end":
      return {
        icon: "check_circle",
        text: `Nodo ${e.node} termina${e.duration_ms != null ? ` · ${e.duration_ms} ms` : ""}`,
      };
    case "llm_call": {
      const taximetro =
        typeof e.cost_usd === "number" && e.tokens_in != null
          ? ` · ${e.tokens_in}→${e.tokens_out} tok · ${fmtUsd(e.cost_usd)} (${e.measured ? "medido" : "estimado"})`
          : "";
      return {
        icon: "smart_toy",
        text: `Llamada LLM: ${providerLabel(e.provider ?? "?", e.model ?? "?")} · ${e.latency_ms} ms · intento ${e.attempts}${taximetro}`,
      };
    }
    case "edge_decision":
      return {
        icon: "alt_route",
        text: `Arista ${e.edge}: ${e.rule} → con ${e.inputs?.impact} · ${
          e.inputs ? Math.round(e.inputs.confidence * 100) : "?"
        }% va a ${e.target === "monitor" ? "Monitoreo" : "Asesor"} (${e.llm_cost})${
          typeof e.saved_usd_est === "number" && e.saved_usd_est > 0
            ? ` · ahorro ≈ ${fmtUsd(e.saved_usd_est)}`
            : ""
        }`,
        highlight: true,
      };
    case "reuse":
      return { icon: "cached", text: `Señal reusada (${e.scope}) — el Analista no vuelve a correr` };
    case "guardrail":
      return { icon: "shield", text: `Guardrail: ${e.field} ${e.action}`, highlight: true };
    case "retry":
      return {
        icon: "restart_alt",
        text: `Rechazada por el Compliance Gate (${(e.violations ?? []).join(", ")}) — reintento ${e.attempt}`,
        highlight: true,
      };
    case "gate":
      return {
        icon: "verified",
        text: `Compliance Gate: ${e.passed}/${e.total} checks · ${
          e.verdict === "corregida" ? "corregida tras auto-corrección" : e.verdict
        }`,
        highlight: true,
      };
    default:
      // Contrato v1: tipos de evento desconocidos (aditivos) se ignoran.
      return null;
  }
}

const CAUSE_LABEL: Record<string, string> = {
  evidencia_insuficiente: "evidencia insuficiente",
  sobre_reaccion_al_precio: "sobre-reacción al precio",
  dato_no_soportado_por_fuente: "dato no soportado por la fuente",
  contexto_faltante: "contexto faltante",
  criterio_del_comite: "criterio del Comité",
};

export default function TraceDrawer({ signal, onClose }: TraceDrawerProps) {
  const [trace, setTrace] = useState<TraceDoc | null>(null);
  const [runIndex, setRunIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [attribution, setAttribution] = useState<Attribution | null>(null);
  const [attribLoading, setAttribLoading] = useState(false);
  const [attribError, setAttribError] = useState<string | null>(null);
  const [replayIndex, setReplayIndex] = useState<number | null>(null);
  const [events, setEvents] = useState<ReviewEvent[]>([]);

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

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-[60]" onClick={onClose} />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Caja de Cristal: expediente de ejecución"
        className="fixed inset-y-0 right-0 w-full max-w-[440px] bg-surface-container border-l border-outline-variant z-[70] overflow-y-auto p-5"
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="font-headline-md text-headline-md text-on-surface font-bold">
              Caja de Cristal
            </h3>
            <p className="text-label-sm text-on-surface-variant">
              Expediente de ejecución · {signal.instrument} · señal {signal.id}
            </p>
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
          <div className="flex gap-2 mb-4">
            {trace.runs.map((r, i) => (
              <button
                key={i}
                onClick={() => {
                  setRunIndex(i);
                  setReplayIndex(null);
                }}
                className={`px-3 py-1.5 rounded-lg text-label-sm font-bold border ${
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
            <div className="bg-surface-container-low border border-outline-variant rounded-xl p-3 mb-3">
              <PipelineGraph run={visibleRun} />
            </div>

            <button
              className="w-full mb-4 flex items-center justify-center gap-2 px-3 py-1.5 bg-surface-container-low border border-outline-variant rounded-lg text-label-sm font-bold text-on-surface hover:border-primary"
              onClick={() => setReplayIndex(0)}
            >
              <span className="material-symbols-outlined text-sm">smart_display</span>
              {replayIndex != null && replayIndex < run.events.length - 1
                ? "Reproduciendo…"
                : "Reproducir ejecución"}
            </button>

            {compliance && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-label-sm uppercase font-bold text-primary">
                    Compliance Gate — despacho
                  </p>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[11px] font-bold ${
                      compliance.verdict === "marcada"
                        ? "bg-error-container/20 text-error"
                        : compliance.verdict === "corregida"
                          ? "bg-warning/20 text-warning"
                          : "bg-success/15 text-success"
                    }`}
                  >
                    {compliance.passed}/{compliance.total}
                    {compliance.verdict === "corregida" && " · corregida"}
                    {compliance.verdict === "marcada" && " · marcada"}
                  </span>
                </div>
                <ul className="space-y-1">
                  {compliance.checks.map((c) => (
                    <li
                      key={c.item}
                      className="flex items-start gap-2 text-body-md text-on-surface-variant"
                      title={c.rule}
                    >
                      <span
                        className={`material-symbols-outlined text-sm mt-0.5 ${
                          c.passed ? "text-success" : "text-error"
                        }`}
                      >
                        {c.passed ? "check_circle" : "cancel"}
                      </span>
                      <span>
                        <b>{c.item.replace(/_/g, " ")}</b> — {c.detail}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="mb-4">
              <p className="text-label-sm uppercase font-bold text-primary mb-2">
                Registrado por el orquestador
              </p>
              <p className="text-label-sm text-on-surface-variant mb-2">
                {providerLabel(run.llm_mode, run.model)} ·{" "}
                {new Date(run.started_at).toLocaleString("es-EC")}
                {(() => {
                  const { cost, saved } = runCostSummary(run);
                  return (
                    <>
                      {" · costo "}
                      {fmtUsd(cost)}
                      {saved > 0 && ` · ahorró ≈ ${fmtUsd(saved)} (ruteo)`}
                    </>
                  );
                })()}
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
                        <span className="font-mono-data text-mono-data mr-2">{e.t_ms}ms</span>
                        {line.text}
                      </span>
                    </li>
                  );
                })}
              </ol>
            </div>

            <div className="mb-4">
              <p className="text-label-sm uppercase font-bold text-on-surface-variant mb-2">
                Declarado por el modelo (lo revisa un humano)
              </p>
              <div className="bg-surface-container-low border border-outline-variant rounded-xl p-3 space-y-2">
                <p className="text-body-md text-on-surface">
                  Impacto <b>{signal.impact}</b> · confianza {formatConfidence(signal.confidence)}
                </p>
                {run.reasoning && (
                  <p className="text-body-md text-on-surface-variant italic">“{run.reasoning}”</p>
                )}
              </div>
            </div>

            {events.length > 0 && (
              <div className="mb-4">
                <p className="text-label-sm uppercase font-bold text-primary mb-2">
                  Expediente de revisión (cadena de custodia)
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

            <div className="mb-2">
              <div className="flex items-center justify-between mb-2">
                <p className="text-label-sm uppercase font-bold text-primary">¿Qué pesó más?</p>
                {!attribution && (
                  <button
                    className="px-3 py-1.5 bg-primary-container text-on-primary-container text-label-sm font-bold rounded-lg disabled:opacity-40"
                    disabled={attribLoading}
                    onClick={loadAttribution}
                  >
                    {attribLoading ? "Sondeando…" : "Sondear"}
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
                      <span className="material-symbols-outlined text-sm mr-1 align-middle">
                        science
                      </span>
                      {p.label}: <b>{p.impact}</b> · {formatConfidence(p.confidence)}
                      {p.impact !== attribution.base.impact && " — el impacto no se sostiene"}
                    </p>
                  ))}
                  {run.llm_mode !== attribution.llm_mode && (
                    <p className="text-label-sm text-error">
                      Sondeo con proveedor distinto al original ({attribution.llm_mode} vs{" "}
                      {run.llm_mode}).
                    </p>
                  )}
                  <p className="text-label-sm text-on-surface-variant">{attribution.note}</p>
                </div>
              )}
            </div>
          </>
        )}
      </aside>
    </>
  );
}
