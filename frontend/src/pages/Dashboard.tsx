import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import ImpactBadge from "../components/ImpactBadge";
import SentimentDonut from "../components/SentimentDonut";
import Skeleton from "../components/Skeleton";
import type { Impact, Instrument, NewsItem, Signal } from "../types";

const NAV_CARDS = [
  { to: "/radar", title: "News Radar", desc: "HU1 · Noticias por activo, sector o tema", icon: "analytics" },
  { to: "/analysis", title: "AI Analysis", desc: "HU2 · Señal explicable de impacto", icon: "psychology" },
  { to: "/briefings", title: "Briefings", desc: "HU3 · Revisión humana y tareas", icon: "description" },
];

const EMPTY_COUNTS: Record<Impact, number> = { positive: 0, negative: 0, neutral: 0, uncertain: 0 };

export default function Dashboard() {
  const [newsToday, setNewsToday] = useState<NewsItem[]>([]);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getNews({ max_age_days: 1 }).catch(() => []),
      api.getInstruments().catch(() => []),
      api.getSignals().catch(() => []),
    ]).then(([news, instrumentsList, signalsList]) => {
      setNewsToday(news);
      setInstruments(instrumentsList);
      setSignals(signalsList);
      setLoading(false);
    });
  }, []);

  const positiveCount = signals.filter((s) => s.impact === "positive").length;
  const sentimentCounts = signals.reduce(
    (acc, s) => ({ ...acc, [s.impact]: acc[s.impact] + 1 }),
    { ...EMPTY_COUNTS },
  );
  const recentActivity = signals.slice(0, 5);

  return (
    <div className="pt-24 pb-stack-lg px-container-padding flex-1">
      <h2 className="font-display-md text-display-md text-on-surface font-bold mb-2">
        Financial Market Intelligence
      </h2>
      <p className="text-body-lg text-on-surface-variant mb-stack-lg">
        Monitorea noticias, analiza impacto y genera briefings con IA para revisión humana — Track 5.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-stack-lg">
        {loading ? (
          <>
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
          </>
        ) : (
          <>
            <div className="bg-surface-container border border-outline-variant rounded-xl p-4">
              <p className="text-label-sm text-on-surface-variant uppercase font-bold mb-1">
                Noticias analizadas hoy
              </p>
              <p className="font-display-md text-display-md text-on-surface">{newsToday.length}</p>
            </div>
            <div className="bg-surface-container border border-outline-variant rounded-xl p-4">
              <p className="text-label-sm text-on-surface-variant uppercase font-bold mb-1">
                Activos monitoreados
              </p>
              <p className="font-display-md text-display-md text-on-surface">{instruments.length}</p>
            </div>
            <div className="bg-surface-container border border-outline-variant rounded-xl p-4">
              <p className="text-label-sm text-on-surface-variant uppercase font-bold mb-1">
                Señales positivas
              </p>
              <p className="font-display-md text-display-md text-on-surface">{positiveCount}</p>
            </div>
          </>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-stack-lg">
        <div className="xl:col-span-2 bg-surface-container border border-outline-variant rounded-xl p-5">
          <h3 className="font-headline-md text-headline-md text-on-surface mb-4">Actividad reciente</h3>
          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-10" />
              <Skeleton className="h-10" />
              <Skeleton className="h-10" />
            </div>
          ) : recentActivity.length === 0 ? (
            <p className="text-body-md text-on-surface-variant">
              Aún no se ha generado ninguna señal — prueba en{" "}
              <Link to="/analysis" className="text-primary underline">
                AI Analysis
              </Link>
              .
            </p>
          ) : (
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-outline-variant">
                  <th className="pb-2 text-label-sm text-on-surface-variant uppercase">Activo</th>
                  <th className="pb-2 text-label-sm text-on-surface-variant uppercase">Impacto</th>
                  <th className="pb-2 text-label-sm text-on-surface-variant uppercase">Confianza</th>
                  <th className="pb-2 text-label-sm text-on-surface-variant uppercase">Estado</th>
                </tr>
              </thead>
              <tbody>
                {recentActivity.map((s) => (
                  <tr key={s.id} className="border-b border-outline-variant last:border-0">
                    <td className="py-2 font-mono-data text-mono-data text-primary">{s.instrument}</td>
                    <td className="py-2">
                      <ImpactBadge impact={s.impact} />
                    </td>
                    <td className="py-2 font-mono-data text-mono-data text-on-surface">
                      {Math.round(s.confidence * 100)}%
                    </td>
                    <td className="py-2 text-label-sm text-on-surface-variant">{s.review_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="bg-surface-container border border-outline-variant rounded-xl p-5 flex flex-col items-center">
          <h3 className="font-headline-md text-headline-md text-on-surface mb-4 self-start">
            Distribución de sentimiento
          </h3>
          {loading ? (
            <Skeleton className="w-[140px] h-[140px] rounded-full" />
          ) : (
            <SentimentDonut counts={sentimentCounts} />
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {NAV_CARDS.map((c) => (
          <Link
            key={c.to}
            to={c.to}
            className="flex flex-col gap-3 bg-surface-container border border-outline-variant rounded-xl p-5 hover:border-primary transition-colors"
          >
            <span className="material-symbols-outlined text-primary text-3xl">{c.icon}</span>
            <h3 className="font-headline-md text-headline-md text-on-surface">{c.title}</h3>
            <p className="text-body-md text-on-surface-variant">{c.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
