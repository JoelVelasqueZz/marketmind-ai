import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import ConfidenceRing from "../components/ConfidenceRing";
import Disclaimer from "../components/Disclaimer";
import ImpactBadge from "../components/ImpactBadge";
import ReviewControls, { STATUS_LABEL } from "../components/ReviewControls";
import Sparkline from "../components/Sparkline";
import { formatPct } from "../lib/format";
import type { Instrument, NewsItem, ReviewStatus, Signal } from "../types";

export default function Signals() {
  const [searchParams] = useSearchParams();
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [newsByInstrument, setNewsByInstrument] = useState<NewsItem[]>([]);
  const [selectedInstrument, setSelectedInstrument] = useState("");
  const [selectedNewsId, setSelectedNewsId] = useState("");

  const [current, setCurrent] = useState<Signal | null>(null);
  const [currentNews, setCurrentNews] = useState<NewsItem | null>(null);
  const [priceHistory, setPriceHistory] = useState<number[]>([]);
  const [history, setHistory] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getInstruments().then(setInstruments).catch(() => setInstruments([]));
    api.getSignals().then(setHistory).catch(() => setHistory([]));
  }, []);

  useEffect(() => {
    if (!selectedInstrument) {
      setNewsByInstrument([]);
      return;
    }
    api.getNews({ asset: selectedInstrument }).then((items) => {
      setNewsByInstrument(items);
      setSelectedNewsId(items[0]?.id ?? "");
    });
  }, [selectedInstrument]);

  async function handleReview(signalId: string, status: ReviewStatus, justification: string) {
    if (status === "pending") return;
    const updated = await api.reviewSignal(signalId, status, justification);
    setCurrent((prev) => (prev && prev.id === signalId ? updated : prev));
    setHistory((prev) => prev.map((s) => (s.id === signalId ? updated : s)));
  }

  async function generate(newsId: string, instrument: string) {
    setLoading(true);
    setError(null);
    try {
      const news = await api.getNews({ asset: instrument }).then((items) =>
        items.find((n) => n.id === newsId) ?? items[0] ?? null,
      );
      const signal = await api.generateSignal(newsId, instrument);
      setCurrent(signal);
      setCurrentNews(news);
      setHistory((prev) => [signal, ...prev]);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!current) {
      setPriceHistory([]);
      return;
    }
    api
      .getPriceHistory(current.instrument, 14)
      .then((points) => setPriceHistory(points.map((p) => p.close)))
      .catch(() => setPriceHistory([]));
  }, [current]);

  useEffect(() => {
    const newsParam = searchParams.get("news");
    const instrumentParam = searchParams.get("instrument");
    const signalParam = searchParams.get("signal");
    if (signalParam) {
      // Viene del boton "Ver analisis" de una tarea: no genera nada nuevo,
      // solo busca la senal ya existente (por eso espera a que "history" cargue).
      return;
    }
    if (newsParam && instrumentParam) {
      setSelectedInstrument(instrumentParam);
      setSelectedNewsId(newsParam);
      generate(newsParam, instrumentParam);
    } else if (instrumentParam) {
      // Viene del boton "Analizar" de Watchlist: solo preseleccionamos el
      // instrumento, el usuario elige la noticia y genera manualmente.
      setSelectedInstrument(instrumentParam);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  useEffect(() => {
    const signalParam = searchParams.get("signal");
    if (!signalParam || history.length === 0 || current?.id === signalParam) return;
    const found = history.find((s) => s.id === signalParam);
    if (!found) return;
    setCurrent(found);
    setSelectedInstrument(found.instrument);
    api
      .getNews({ asset: found.instrument })
      .then((items) => setCurrentNews(items.find((n) => n.id === found.news_id) ?? null))
      .catch(() => setCurrentNews(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, history]);

  return (
    <div className="pt-24 pb-stack-lg px-container-padding flex-1">
      <div className="mb-stack-lg">
        <h2 className="font-headline-lg text-headline-lg text-on-surface font-bold">AI Analysis</h2>
        <p className="text-body-md text-on-surface-variant">
          Señal explicable de impacto del Analista de Coyuntura de Mercados IA — HU2.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-stack-sm mb-stack-lg bg-surface-container-low p-4 rounded-xl border border-outline-variant">
        <div className="flex flex-col gap-1">
          <span className="text-label-sm text-on-surface-variant">Instrumento</span>
          <select
            className="bg-surface-variant border border-outline-variant rounded-lg px-3 py-2 text-label-md font-bold text-on-surface outline-none cursor-pointer"
            value={selectedInstrument}
            onChange={(e) => setSelectedInstrument(e.target.value)}
          >
            <option value="">Selecciona…</option>
            {instruments.map((i) => (
              <option key={i.symbol} value={i.symbol}>
                {i.symbol} — {i.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1 flex-1 min-w-[240px]">
          <span className="text-label-sm text-on-surface-variant">Noticia</span>
          <select
            className="bg-surface-variant border border-outline-variant rounded-lg px-3 py-2 text-label-md text-on-surface outline-none cursor-pointer disabled:opacity-40"
            value={selectedNewsId}
            disabled={newsByInstrument.length === 0}
            onChange={(e) => setSelectedNewsId(e.target.value)}
          >
            {newsByInstrument.map((n) => (
              <option key={n.id} value={n.id}>
                {n.headline}
              </option>
            ))}
          </select>
        </div>
        <button
          className="px-4 py-2 bg-primary-container text-on-primary-container text-label-md font-bold rounded-lg disabled:opacity-40"
          disabled={!selectedInstrument || !selectedNewsId || loading}
          onClick={() => generate(selectedNewsId, selectedInstrument)}
        >
          {loading ? "Analizando…" : "Generar análisis"}
        </button>
      </div>

      {error && <div className="mb-stack-md text-body-md text-error">Error: {error}</div>}

      {current && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-stack-lg">
          <div className="lg:col-span-2 bg-surface-container border border-outline-variant rounded-xl p-5">
            {currentNews && (
              <>
                <span className="text-label-sm text-primary uppercase">{currentNews.sector}</span>
                <h3 className="font-headline-lg text-headline-lg text-on-surface my-2">
                  {currentNews.headline}
                </h3>
                <p className="text-body-md text-on-surface-variant mb-4">{currentNews.summary}</p>
              </>
            )}
            <div className="flex items-center gap-4 mb-4">
              <ImpactBadge impact={current.impact} />
              <span className="text-label-sm text-on-surface-variant">
                Fuentes: {current.sources.join(", ")}
              </span>
            </div>

            <h4 className="text-label-sm text-on-surface-variant uppercase font-bold mb-2">
              Evidencia
            </h4>
            <ul className="space-y-2 mb-4">
              {current.evidence.map((e, idx) => (
                <li key={idx} className="flex items-start gap-2 text-body-md text-on-surface">
                  <span className="material-symbols-outlined text-success text-sm mt-0.5">
                    check_circle
                  </span>
                  {e}
                </li>
              ))}
            </ul>

            <div className="bg-surface-container-low rounded-lg p-4 mb-4 flex items-center justify-between gap-4">
              <div>
                <p className="text-label-sm text-on-surface-variant uppercase font-bold mb-1">
                  Comparación de precio
                </p>
                <p className="font-mono-data text-mono-data text-on-surface">
                  {current.price_comparison.instrument} {formatPct(current.price_comparison.change_pct)}
                  {" · "}
                  {current.price_comparison.window_days}d
                </p>
                <p className="text-body-md text-on-surface-variant mt-1">
                  {current.price_comparison.note}
                </p>
              </div>
              <Sparkline points={priceHistory} width={120} height={36} />
            </div>

            {current.suggested_action && (
              <div className="flex items-start gap-2 bg-primary-container/10 border border-primary/30 rounded-lg p-3 mb-4">
                <span className="material-symbols-outlined text-primary">lightbulb</span>
                <p className="text-body-md text-on-surface">{current.suggested_action}</p>
              </div>
            )}

            <Disclaimer text={current.disclaimer} />
          </div>

          <div className="bg-surface-container border border-outline-variant rounded-xl p-5 flex flex-col items-center gap-4">
            <p className="text-label-sm text-on-surface-variant uppercase font-bold self-start">
              Confianza
            </p>
            <ConfidenceRing confidence={current.confidence} size={96} />
            <div className="w-full">
              <ReviewControls
                key={current.id}
                currentStatus={current.review_status}
                currentJustification={current.review_justification}
                onSave={(status, justification) => handleReview(current.id, status, justification)}
              />
            </div>
          </div>
        </div>
      )}

      <h3 className="font-headline-md text-headline-md text-on-surface mb-3">Señales generadas</h3>
      <div className="space-y-2">
        {history.length === 0 && (
          <p className="text-body-md text-on-surface-variant">Aún no se ha generado ninguna señal.</p>
        )}
        {history.map((s) => (
          <button
            key={s.id}
            onClick={() => {
              setCurrent(s);
              setCurrentNews(null);
            }}
            className="w-full flex items-center justify-between bg-surface-container-low hover:bg-surface-container-high border border-outline-variant rounded-lg px-4 py-3 text-left transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className="font-mono-data text-mono-data text-primary">{s.instrument}</span>
              <ImpactBadge impact={s.impact} />
            </div>
            <span className="text-label-sm text-on-surface-variant">{STATUS_LABEL[s.review_status]}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
