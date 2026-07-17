import type { Triage, TriageLevel } from "../types";

const STYLES: Record<TriageLevel, { bg: string; text: string; dot: string; label: string }> = {
  rojo: { bg: "bg-error-container/20", text: "text-error", dot: "bg-error", label: "Rojo" },
  naranja: { bg: "bg-warning/20", text: "text-warning", dot: "bg-warning", label: "Naranja" },
  amarillo: { bg: "bg-yellow-400/10", text: "text-yellow-400", dot: "bg-yellow-400", label: "Amarillo" },
  verde: { bg: "bg-success/15", text: "text-success", dot: "bg-success", label: "Verde" },
  // Azul con borde (sin relleno) para no confundirse con el ImpactBadge
  // "Positivo", que usa la misma píldora primary rellena.
  azul: { bg: "bg-transparent border border-primary/50", text: "text-primary", dot: "bg-primary", label: "Azul" },
};

// Triaje estilo Manchester: nivel + SLA, con la fórmula literal en el tooltip.
export default function TriageBadge({ triage }: { triage: Triage }) {
  const s = STYLES[triage.level];
  return (
    <div
      className={`px-2 py-0.5 ${s.bg} ${s.text} text-[11px] font-bold rounded-full flex items-center gap-1 w-fit whitespace-nowrap`}
      title={`Regla: ${triage.rule}`}
    >
      <span className={`w-1.5 h-1.5 ${s.dot} rounded-full`} />
      {s.label} · {triage.sla}
    </div>
  );
}
