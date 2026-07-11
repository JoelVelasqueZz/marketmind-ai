export function formatAge(ageDays: number): string {
  if (ageDays < 1 / 24) return `${Math.max(1, Math.round(ageDays * 24 * 60))}m ago`;
  if (ageDays < 1) return `${Math.round(ageDays * 24)}h ago`;
  if (ageDays < 30) return `${Math.round(ageDays)}d ago`;
  return `${Math.round(ageDays / 30)}mo ago`;
}

export function formatPct(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatPrice(value: number): string {
  return value >= 1000 ? value.toLocaleString("en-US", { maximumFractionDigits: 0 }) : value.toFixed(2);
}
