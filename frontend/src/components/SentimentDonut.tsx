import type { Impact } from "../types";

const COLORS: Record<Impact, string> = {
  positive: "#7dd88f",
  negative: "#ffb4ab",
  neutral: "#8d90a0",
  uncertain: "#f5c065",
};

const LABELS: Record<Impact, string> = {
  positive: "Positivo",
  negative: "Negativo",
  neutral: "Neutral",
  uncertain: "Incierto",
};

interface SentimentDonutProps {
  counts: Record<Impact, number>;
  size?: number;
}

export default function SentimentDonut({ counts, size = 140 }: SentimentDonutProps) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const stroke = 16;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;

  const order: Impact[] = ["positive", "negative", "neutral", "uncertain"];
  let offsetAcc = 0;
  const segments = order
    .filter((k) => counts[k] > 0)
    .map((k) => {
      const fraction = total ? counts[k] / total : 0;
      const dash = fraction * circumference;
      const segment = { key: k, dash, offset: offsetAcc, color: COLORS[k] };
      offsetAcc += dash;
      return segment;
    });

  const top = total
    ? order
        .filter((k) => counts[k] > 0)
        .sort((a, b) => counts[b] - counts[a])[0]
    : null;
  const topPct = top ? Math.round((counts[top] / total) * 100) : 0;

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#2e3544" strokeWidth={stroke} />
          {segments.map((s) => (
            <circle
              key={s.key}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={s.color}
              strokeWidth={stroke}
              strokeDasharray={`${s.dash} ${circumference - s.dash}`}
              strokeDashoffset={-s.offset}
            />
          ))}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {total === 0 ? (
            <span className="text-body-md text-on-surface-variant">Sin datos</span>
          ) : (
            <>
              <span className="font-display-md text-headline-lg text-on-surface font-bold">{topPct}%</span>
              <span className="text-label-sm text-on-surface-variant">{LABELS[top!]}</span>
            </>
          )}
        </div>
      </div>
      <div className="flex flex-wrap justify-center gap-3">
        {order
          .filter((k) => counts[k] > 0)
          .map((k) => (
            <div key={k} className="flex items-center gap-1.5 text-label-sm text-on-surface-variant">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[k] }} />
              {LABELS[k]} {total ? Math.round((counts[k] / total) * 100) : 0}%
            </div>
          ))}
      </div>
    </div>
  );
}
