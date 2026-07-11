export type InstrumentType = "equity" | "credit" | "crypto" | "other";
export type Impact = "positive" | "negative" | "neutral" | "uncertain";
export type ReviewStatus = "pending" | "revisada" | "escalada" | "descartada";

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

export interface TaskAlert {
  id: string;
  signal_id?: string | null;
  instrument: string;
  title: string;
  description: string;
  status: "open" | "done";
  created_at: string;
}
