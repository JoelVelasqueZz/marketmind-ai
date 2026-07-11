interface ConfidenceRingProps {
  confidence: number; // 0..1
  size?: number;
}

export default function ConfidenceRing({ confidence, size = 64 }: ConfidenceRingProps) {
  const pct = Math.round(confidence * 100);
  const color = pct <= 40 ? "#ffb4ab" : pct <= 75 ? "#f5c065" : "#7dd88f";
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - confidence);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#434655"
          strokeWidth={4}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={4}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center font-mono-data text-mono-data text-on-surface">
        {pct}%
      </div>
    </div>
  );
}
