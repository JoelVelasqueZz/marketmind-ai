import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import ImpactBadge from "../components/ImpactBadge";
import { STATUS_LABEL } from "../components/ReviewControls";
import SentimentDonut from "../components/SentimentDonut";
import Skeleton from "../components/Skeleton";
import { CAUSE_LABELS } from "../lib/causes";
import type { Impact, Instrument, ReviewCause, Signal, TriageLevel } from "../types";

const TRIAGE_ORDER: TriageLevel[] = ["rojo", "naranja", "amarillo", "verde", "azul"];
const TRIAGE_DOT: Record<TriageLevel, string> = {
  rojo: "bg-error",
  naranja: "bg-warning",
  amarillo: "bg-yellow-400",
  verde: "bg-success",
  azul: "bg-primary",
};

const NAV_CARDS = [
  { to: "/radar", title: "News Radar", desc: "HU1 · Noticias por activo, sector o tema", icon: "analytics" },
  { to: "/analysis", title: "AI Analysis", desc: "HU2 · Señal explicable de impacto", icon: "psychology" },
  { to: "/briefings", title: "Briefings", desc: "HU3 · Revisión humana y tareas", icon: "description" },
];

const EMPTY_COUNTS: Record<Impact, number> = { positive: 0, negative: 0, neutral: 0, uncertain: 0 };

export default function Dashboard() {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [reviewCauses, setReviewCauses] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    Promise.all([api.getInstruments(), api.getSignals(), api.getReviewCauses()])
      .then(([instrumentsList, signalsList, causes]) => {
        setInstruments(instrumentsList);
        setSignals(signalsList);
        setReviewCauses(causes);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  // Noticias distintas que ya tienen al menos una senal generada (no "noticias
  // publicadas en las ultimas 24h" — los datos mock tienen fechas fijas, asi que
  // ese filtro casi siempre da 0 sin importar cuanta actividad real haya).
  const newsAnalyzedCount = new Set(signals.map((s) => s.news_id)).size;
  const positiveCount = signals.filter((s) => s.impact === "positive").length;
  const sentimentCounts = signals.reduce(
    (acc, s) => ({ ...acc, [s.impact]: acc[s.impact] + 1 }),
    { ...EMPTY_COUNTS },
  );
  const recentActivity = signals.slice(0, 5);

  // Track record: ¿la direccion que clasifico el Analista coincide con el movimiento de
  // precio real que se le mostro? "uncertain" queda fuera del calculo a proposito, porque
  // ahi el propio agente ya declaro que no hay evidencia suficiente para tomar postura.
  const scoredMatches = signals
    .map((s) => {
      const pct = s.price_comparison.change_pct;
      if (s.impact === "positive") return pct > 0;
      if (s.impact === "negative") return pct < 0;
      if (s.impact === "neutral") return Math.abs(pct) < 1;
      return null;
    })
    .filter((m): m is boolean => m !== null);
  const trackRecordPct =
    scoredMatches.length > 0
      ? Math.round((scoredMatches.filter(Boolean).length / scoredMatches.length) * 100)
      : null;

  return (
    <div className="pt-24 pb-stack-lg px-container-padding flex-1">
      <h2 className="font-display-md text-display-md text-on-surface font-bold mb-2">
        Financial Market Intelligence
      </h2>
      <p className="text-body-lg text-on-surface-variant mb-stack-lg">
        Monitorea noticias, analiza impacto y genera briefings con IA para revisión humana — Track 5.
      </p>

      {error && (
        <div className="mb-stack-lg flex items-center justify-between gap-4 bg-surface-container border border-error/40 rounded-xl p-4">
          <p className="text-body-md text-on-surface">
            No se pudo conectar con el backend (puede estar despertando — el plan gratuito se duerme
            tras inactividad): {error}
          </p>
          <button
            className="px-4 py-2 bg-primary-container text-on-primary-container text-label-md font-bold rounded-lg shrink-0"
            onClick={load}
          >
            Reintentar
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-stack-lg">
        {loading ? (
          <>
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
          </>
        ) : (
          <>
            <div className="bg-surface-container border border-outline-variant rounded-xl p-4">
              <p className="text-label-sm text-on-surface-variant uppercase font-bold mb-1">
                Noticias analizadas
              </p>
              <p className="font-display-md text-display-md text-on-surface">{newsAnalyzedCount}</p>
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
            <div
              className="bg-surface-container border border-outline-variant rounded-xl p-4"
              title="Coincidencia direccional entre la clasificacion del Analista y el movimiento de precio registrado. No es una prediccion ni garantia de resultados futuros."
            >
              <p className="text-label-sm text-on-surface-variant uppercase font-bold mb-1">
                Track record
              </p>
              <p className="font-display-md text-display-md text-on-surface">
                {trackRecordPct === null ? "—" : `${trackRecordPct}%`}
              </p>
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
                    <td className="py-2 text-label-sm text-on-surface-variant">
                      {STATUS_LABEL[s.review_status]}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="bg-surface-container border border-outline-variant rounded-xl p-5 flex flex-col items-center">
          <h3 className="font-headline-md text-headline-md text-on-surface mb-4 self-start">
            Señales por tipo de impacto
          </h3>
          {loading ? (
            <Skeleton className="w-[140px] h-[140px] rounded-full" />
          ) : (
            <SentimentDonut counts={sentimentCounts} />
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-stack-lg">
        <div
          className="bg-surface-container border border-outline-variant rounded-xl p-5"
          title="Triaje estilo Manchester: cada señal recibe nivel y SLA por una regla literal reproducible. El azul es la arista de monitoreo ($0 LLM)."
        >
          <h3 className="font-headline-md text-headline-md text-on-surface mb-1">Triaje de la cola</h3>
          <p className="text-label-sm text-on-surface-variant mb-4">
            A qué debe mirar primero el humano — niveles con SLA, calculados por reglas literales.
          </p>
          {loading ? (
            <Skeleton className="h-10" />
          ) : (
            <div className="flex flex-wrap gap-4">
              {TRIAGE_ORDER.map((level) => {
                const count = signals.filter((s) => s.triage?.level === level).length;
                return (
                  <div key={level} className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${TRIAGE_DOT[level]}`} />
                    <span className="text-body-md text-on-surface capitalize">{level}</span>
                    <span className="font-mono-data text-mono-data text-on-surface-variant">{count}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div
          className="bg-surface-container border border-outline-variant rounded-xl p-5"
          title="Taxonomía NTSB: causa raíz elegida por el Comité al descartar o escalar. Alimenta el few-shot del Analista."
        >
          <h3 className="font-headline-md text-headline-md text-on-surface mb-1">
            ¿De qué se equivoca el Analista?
          </h3>
          <p className="text-label-sm text-on-surface-variant mb-4">
            Causas raíz según el Comité — el sistema publica sus propios modos de fallo.
          </p>
          {loading ? (
            <Skeleton className="h-10" />
          ) : Object.keys(reviewCauses).length === 0 ? (
            <p className="text-body-md text-on-surface-variant">
              Aún sin causas registradas: al descartar o escalar una señal, elige la causa raíz.
            </p>
          ) : (
            <div className="space-y-2">
              {Object.entries(reviewCauses)
                .sort((a, b) => b[1] - a[1])
                .map(([cause, count]) => (
                  <div key={cause} className="flex items-center gap-3">
                    <span className="text-body-md text-on-surface flex-1">
                      {CAUSE_LABELS[cause as ReviewCause] ?? cause}
                    </span>
                    <div className="flex items-center gap-2">
                      <div
                        className="h-2 bg-primary rounded-full"
                        style={{
                          width: `${Math.max(12, (count / Math.max(...Object.values(reviewCauses))) * 120)}px`,
                        }}
                      />
                      <span className="font-mono-data text-mono-data text-on-surface-variant">{count}</span>
                    </div>
                  </div>
                ))}
            </div>
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
