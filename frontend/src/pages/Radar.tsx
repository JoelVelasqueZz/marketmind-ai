import { useEffect, useState } from "react";
import { api } from "../api";
import Disclaimer from "../components/Disclaimer";
import Filters, { type FilterState } from "../components/Filters";
import NewsCard from "../components/NewsCard";
import type { Instrument, NewsItem } from "../types";

const EMPTY_FILTERS: FilterState = { type: "", asset: "", maxAgeDays: "" };

export default function Radar() {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getInstruments().then(setInstruments).catch(() => setInstruments([]));
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .getNews({
        type: filters.type || undefined,
        asset: filters.asset || undefined,
        max_age_days: filters.maxAgeDays ? Number(filters.maxAgeDays) : undefined,
      })
      .then(setNews)
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, [filters]);

  return (
    <div className="pt-24 pb-stack-lg px-container-padding flex-1">
      <div className="mb-stack-lg">
        <h2 className="font-headline-lg text-headline-lg text-on-surface font-bold">News Radar</h2>
        <p className="text-body-md text-on-surface-variant">
          Noticias recientes relacionadas a instrumentos financieros — HU1.
        </p>
      </div>

      <Filters instruments={instruments} value={filters} onChange={setFilters} />

      {error && (
        <div className="mb-stack-md text-body-md text-error">No se pudo cargar el radar: {error}</div>
      )}

      {loading ? (
        <p className="text-body-md text-on-surface-variant">Cargando noticias…</p>
      ) : news.length === 0 ? (
        <p className="text-body-md text-on-surface-variant">
          No hay noticias que coincidan con estos filtros.
        </p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-stack-lg">
          {news.map((item) => (
            <NewsCard key={item.id} news={item} />
          ))}
        </div>
      )}

      <Disclaimer text="Feed de prueba con fuentes nombradas (Reuters, Bloomberg, CNBC, CoinDesk, FT, WSJ) — datos ficticios para demo." />
    </div>
  );
}
