interface SparklineProps {
  points: number[];
  width?: number;
  height?: number;
}

export default function Sparkline({ points, width = 96, height = 28 }: SparklineProps) {
  if (points.length < 2) {
    return <div style={{ width, height }} className="text-on-surface-variant text-label-sm">—</div>;
  }

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const trendUp = points[points.length - 1] >= points[0];
  const color = trendUp ? "#7dd88f" : "#ffb4ab";

  const step = width / (points.length - 1);
  const coords = points.map((v, i) => {
    const x = i * step;
    const y = height - ((v - min) / range) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const areaPath = `M0,${height} L${coords.join(" L")} L${width},${height} Z`;

  return (
    <svg width={width} height={height} role="img" aria-label="Historial de precio">
      <path d={areaPath} fill={color} opacity={0.12} />
      <polyline points={coords.join(" ")} fill="none" stroke={color} strokeWidth={1.5} />
    </svg>
  );
}
