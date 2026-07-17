export type InstrumentType = "equity" | "credit" | "crypto" | "other";
export type Impact = "positive" | "negative" | "neutral" | "uncertain";
export type ReviewStatus = "pending" | "revisada" | "escalada" | "descartada";

export type ReviewCause =
  | "evidencia_insuficiente"
  | "sobre_reaccion_al_precio"
  | "dato_no_soportado_por_fuente"
  | "contexto_faltante"
  | "criterio_del_comite";

export type ReviewerRole = "analista" | "lead" | "compliance";

export interface GateCheck {
  item: string;
  passed: boolean;
  detail: string;
  rule: string;
}

export interface Compliance {
  verdict: "ok" | "corregida" | "marcada";
  passed: number;
  total: number;
  checks: GateCheck[];
}

export interface ReviewEvent {
  from_status: string;
  to_status: string;
  reviewer: string;
  role: string;
  cause?: string | null;
  justification: string;
  at: string;
}

export type TriageLevel = "rojo" | "naranja" | "amarillo" | "verde" | "azul";

export interface Triage {
  level: TriageLevel;
  priority: number;
  sla: string;
  rule: string;
}

export interface Freshness {
  pct: number;
  age_days: number;
  half_life_days: number;
  stale: boolean;
  rule: string;
}

export interface Instrument {
  symbol: string;
  name: string;
  type: InstrumentType;
  sector: string;
}

export interface NewsItem {
  id: string;
  headline: string;
  summary: string;
  source: string;
  published_at: string;
  instruments: string[];
  sector: string;
  topic: string;
  age_days: number;
}

export interface PriceComparison {
  instrument: string;
  change_pct: number;
  window_days: number;
  note: string;
}

export interface PricePoint {
  date: string;
  close: number;
}

export interface ReviewExample {
  instrument: string;
  impact: Impact;
  confidence: number;
  evidence: string[];
  review_status: ReviewStatus;
  review_justification: string;
}

export interface Signal {
  id: string;
  news_id: string;
  instrument: string;
  impact: Impact;
  confidence: number;
  evidence: string[];
  sources: string[];
  price_comparison: PriceComparison;
  disclaimer: string;
  suggested_action?: string | null;
  created_at: string;
  review_status: ReviewStatus;
  review_justification?: string | null;
  review_cause?: ReviewCause | null;
  reviewed_by?: string | null;
  review_examples_used: ReviewExample[];
  has_trace: boolean;
  has_attribution: boolean;
  compliance?: Compliance | null;
  triage?: Triage | null;
  freshness?: Freshness | null;
}

// --- Caja de Cristal: traza de ejecucion escrita por el orquestador ---

export interface TraceEvent {
  t_ms: number;
  type: string;
  node?: string;
  edge?: string;
  rule?: string;
  inputs?: { impact: Impact; confidence: number };
  threshold?: number;
  target?: string;
  llm_cost?: string;
  provider?: string;
  model?: string;
  latency_ms?: number;
  attempts?: number;
  tokens_in?: number;
  tokens_out?: number;
  cost_usd?: number;
  measured?: boolean;
  saved_usd_est?: number;
  duration_ms?: number;
  output_digest?: Record<string, unknown>;
  signal_id?: string;
  scope?: string;
  field?: string;
  action?: string;
  passed?: number;
  total?: number;
  verdict?: string;
  reason?: string;
  attempt?: number;
  violations?: string[];
}

export interface TraceRun {
  llm_mode: string;
  model: string;
  path: "analysis" | "briefing" | "briefing-reuse";
  started_at: string;
  truncated: boolean;
  reasoning?: string | null;
  events: TraceEvent[];
}

export interface TraceDoc {
  v: number;
  runs: TraceRun[];
}

export interface AttributionProbe {
  key: string;
  label: string;
  impact: Impact;
  confidence: number;
}

export interface Attribution {
  v: number;
  llm_mode: string;
  model: string;
  generated_at: string;
  base: { impact: Impact; confidence: number };
  probes: AttributionProbe[];
  note: string;
}

export interface BriefingItem {
  instrument: string;
  signal: Signal;
  news_headline: string;
  price_change_pct: number;
  research_action: string;
  executive_summary: string[];
}

export interface Briefing {
  watchlist_id: string;
  watchlist_name: string;
  generated_at: string;
  items: BriefingItem[];
  disclaimer: string;
}

export interface Watchlist {
  id: string;
  name: string;
  instruments: string[];
}

export interface AssetSignalSummary {
  impact: Impact;
  confidence: number;
  created_at: string;
}

export interface AssetOverview {
  symbol: string;
  name: string;
  type: InstrumentType;
  price: number | null;
  change_pct_1d: number | null;
  signal: AssetSignalSummary | null;
}

export interface WatchlistOverview {
  watchlist_id: string;
  watchlist_name: string;
  assets: AssetOverview[];
}

export interface Health {
  status: string;
  llm_mode: "mock" | "gemini" | "claude" | "deepseek";
}

export interface TaskAlert {
  id: string;
  signal_id?: string | null;
  instrument: string;
  title: string;
  description: string;
  status: "open" | "done";
  created_at: string;
}
