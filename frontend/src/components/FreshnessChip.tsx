import type { Freshness } from "../types";

interface FreshnessChipProps {
  freshness: Freshness;
  onReevaluate?: () => void;
  reevaluating?: boolean;
}

// Vigencia: la señal declara su propia caducidad. Si está vencida (< 50%),
// ofrece re-evaluar (regeneración con force sobre la misma noticia).
export default function FreshnessChip({ freshness, onReevaluate, reevaluating }: FreshnessChipProps) {
  const pct = Math.round(freshness.pct * 100);
  return (
    <div className="flex items-center gap-2" title={freshness.rule}>
      <span
        className={`px-2 py-0.5 text-[11px] font-bold rounded-full flex items-center gap-1 w-fit ${
          freshness.stale
            ? "bg-warning/20 text-warning"
            : "bg-surface-variant text-on-surface-variant"
        }`}
      >
        <span className="material-symbols-outlined text-[12px]">schedule</span>
        Vigencia {pct}%
      </span>
      {freshness.stale && onReevaluate && (
        <button
          className="text-label-sm font-bold text-primary hover:underline disabled:opacity-40"
          disabled={reevaluating}
          onClick={onReevaluate}
          title="El análisis envejeció: regenerar con datos actuales (traza nueva)"
        >
          {reevaluating ? "Re-evaluando…" : "Re-evaluar"}
        </button>
      )}
    </div>
  );
}
