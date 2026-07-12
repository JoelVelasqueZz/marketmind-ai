import type {
  Briefing,
  Health,
  Instrument,
  NewsItem,
  PricePoint,
  Signal,
  TaskAlert,
  Watchlist,
  WatchlistOverview,
} from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export interface NewsFilters {
  type?: string;
  asset?: string;
  max_age_days?: number;
  sector?: string;
  topic?: string;
  q?: string;
}

function toQuery<T extends object>(params: T): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export const api = {
  getHealth: () => request<Health>("/api/health"),

  getInstruments: () => request<Instrument[]>("/api/instruments"),

  getNews: (filters: NewsFilters = {}) =>
    request<NewsItem[]>(`/api/news${toQuery(filters)}`),

  getSignals: (asset?: string) =>
    request<Signal[]>(`/api/signals${toQuery({ asset })}`),

  generateSignal: (news_id: string, instrument: string) =>
    request<Signal>("/api/signals/generate", {
      method: "POST",
      body: JSON.stringify({ news_id, instrument }),
    }),

  reviewSignal: (signalId: string, status: string, justification: string) =>
    request<Signal>(`/api/signals/${signalId}/review`, {
      method: "POST",
      body: JSON.stringify({ status, justification }),
    }),

  getWatchlists: () => request<Watchlist[]>("/api/briefing/watchlists"),

  getWatchlistOverview: (watchlistId: string) =>
    request<WatchlistOverview>(`/api/briefing/watchlists/${encodeURIComponent(watchlistId)}/overview`),

  generateBriefing: (watchlistId: string) =>
    request<Briefing>(`/api/briefing/generate?watchlist=${encodeURIComponent(watchlistId)}`, {
      method: "POST",
    }),

  getPriceHistory: (symbol: string, days = 14) =>
    request<PricePoint[]>(`/api/prices/${encodeURIComponent(symbol)}?days=${days}`),

  getTasks: () => request<TaskAlert[]>("/api/tasks"),

  completeTask: (taskId: string) =>
    request<TaskAlert>(`/api/tasks/${taskId}/complete`, { method: "POST" }),

  reopenTask: (taskId: string) =>
    request<TaskAlert>(`/api/tasks/${taskId}/reopen`, { method: "POST" }),
};
