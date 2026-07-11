import type { Impact } from "../types";

const STYLES: Record<Impact, { bg: string; text: string; dot: string; label: string }> = {
  positive: { bg: "bg-primary-container/20", text: "text-primary-container", dot: "bg-primary", label: "Positive" },
  negative: { bg: "bg-error-container/20", text: "text-error", dot: "bg-error", label: "Negative" },
  neutral: { bg: "bg-surface-variant", text: "text-on-surface-variant", dot: "bg-on-surface-variant", label: "Neutral" },
  uncertain: { bg: "bg-warning/20", text: "text-warning", dot: "bg-warning", label: "Uncertain" },
};

export default function ImpactBadge({ impact }: { impact: Impact }) {
  const s = STYLES[impact];
  return (
    <div
      className={`px-2 py-0.5 ${s.bg} ${s.text} text-[11px] font-bold rounded-full ai-glow flex items-center gap-1 w-fit`}
    >
      <span className={`w-1.5 h-1.5 ${s.dot} rounded-full animate-pulse`} />
      {s.label}
    </div>
  );
}
