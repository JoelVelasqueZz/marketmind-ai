import { useNavigate } from "react-router-dom";
import { formatAge } from "../lib/format";
import type { NewsItem } from "../types";

interface NewsCardProps {
  news: NewsItem;
}

export default function NewsCard({ news }: NewsCardProps) {
  const navigate = useNavigate();
  const primaryInstrument = news.instruments[0];

  return (
    <article className="flex flex-col bg-surface-container border border-outline-variant rounded-xl p-5 news-card-hover transition-all duration-300">
      <header className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-surface-variant rounded flex items-center justify-center">
            <span className="material-symbols-outlined text-xs text-on-surface-variant">newspaper</span>
          </div>
          <span className="text-label-sm text-on-surface-variant">{news.source}</span>
        </div>
        <span className="text-label-sm text-on-surface-variant opacity-60">{formatAge(news.age_days)}</span>
      </header>

      <h3 className="font-headline-md text-headline-md text-on-surface mb-3 leading-snug">
        {news.headline}
      </h3>
      <p className="text-body-md text-on-surface-variant mb-4 line-clamp-3">{news.summary}</p>

      <div className="flex flex-wrap gap-2 mb-6">
        {news.instruments.map((symbol) => (
          <span
            key={symbol}
            className="font-mono-data text-[10px] px-2 py-0.5 bg-surface-variant text-primary rounded border border-outline-variant"
          >
            {symbol}
          </span>
        ))}
        <span className="font-mono-data text-[10px] px-2 py-0.5 bg-surface-variant text-on-surface-variant rounded border border-outline-variant">
          {news.topic}
        </span>
      </div>

      <footer className="mt-auto pt-4 border-t border-outline-variant flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-wider text-on-surface-variant font-bold">
          {news.sector}
        </span>
        <button
          className="px-4 py-2 bg-surface-variant hover:bg-surface-container-highest text-on-surface text-label-md font-bold rounded-lg transition-colors border border-outline-variant disabled:opacity-40 disabled:cursor-not-allowed"
          disabled={!primaryInstrument}
          onClick={() =>
            navigate(`/analysis?news=${encodeURIComponent(news.id)}&instrument=${encodeURIComponent(primaryInstrument)}`)
          }
        >
          Ver análisis
        </button>
      </footer>
    </article>
  );
}
