import { useEffect, useState } from "react";
import { api } from "../api";
import PipelineGraph from "./PipelineGraph";
import { formatConfidence } from "../lib/format";
import type { Attribution, Signal, TraceDoc, TraceEvent, TraceRun } from "../types";

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
  // En mock el nombre del modelo de config no aplica: el generador es determinista.
  return llmMode === "mock" ? "mock · determinista (sin LLM)" : `${llmMode} · ${model}`;
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
    case "llm_call":
      return {
        icon: "smart_toy",
        text: `Llamada LLM: ${providerLabel(e.provider ?? "?", e.model ?? "?")} · ${e.latency_ms} ms · intento ${e.attempts}`,
      };
    case "edge_decision":
      return {
        icon: "alt_route",
        text: `Arista ${e.edge}: ${e.rule} → con ${e.inputs?.impact} · ${
          e.inputs ? Math.round(e.inputs.confidence * 100) : "?"
        }% va a ${e.target === "monitor" ? "Monitoreo" : "Asesor"} (${e.llm_cost})`,
        highlight: true,
      };
    case "reuse":
      return { icon: "cached", text: `Señal reusada (${e.scope}) — el Analista no vuelve a correr` };
    case "guardrail":
      return {
        icon: "shield",
        text: `Guardrail: ${e.field} ${e.action}`,
        highlight: true,
      };
    default:
      // Contrato v1: tipos de evento desconocidos (aditivos) se ignoran.
      return null;
  }
}

export default function TraceDrawer({ signal, onClose }: TraceDrawerProps) {
  const [trace, setTrace] = useState<TraceDoc | null>(null);
  const [runIndex, setRunIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [attribution, setAttribution] = useState<Attribution | null>(null);
  const [attribLoading, setAttribLoading] = useState(false);
  const [attribError, setAttribError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getSignalTrace(signal.id)
      .then((t) => {
        setTrace(t);
        setRunIndex(t.runs.length - 1);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [signal.id]);

  useEffect(() => {
    // Con el drawer abierto: sin scroll de fondo y Escape cierra.
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

  const run = trace?.runs[runIndex];

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
                onClick={() => setRunIndex(i)}
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

        {run && (
          <>
            <div className="bg-surface-container-low border border-outline-variant rounded-xl p-3 mb-4">
              <PipelineGraph run={run} />
            </div>

            <div className="mb-4">
              <p className="text-label-sm uppercase font-bold text-primary mb-2">
                Registrado por el orquestador
              </p>
              <p className="text-label-sm text-on-surface-variant mb-2">
                {providerLabel(run.llm_mode, run.model)} ·{" "}
                {new Date(run.started_at).toLocaleString("es-EC")}
                {run.truncated && " · traza recortada"}
              </p>
              <ol className="space-y-2">
                {run.events.map((e, idx) => {
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
