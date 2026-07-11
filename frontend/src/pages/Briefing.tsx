import { useEffect, useState } from "react";
import { api } from "../api";
import Disclaimer from "../components/Disclaimer";
import ImpactBadge from "../components/ImpactBadge";
import ReviewControls from "../components/ReviewControls";
import { formatPct } from "../lib/format";
import type { Briefing as BriefingType, ReviewStatus, TaskAlert, Watchlist } from "../types";

export default function Briefing() {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [selected, setSelected] = useState("");
  const [briefing, setBriefing] = useState<BriefingType | null>(null);
  const [tasks, setTasks] = useState<TaskAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getWatchlists().then((w) => {
      setWatchlists(w);
      if (w[0]) setSelected(w[0].id);
    });
    refreshTasks();
  }, []);

  function refreshTasks() {
    api.getTasks().then(setTasks).catch(() => setTasks([]));
  }

  async function generate(watchlistId: string) {
    setLoading(true);
    setError(null);
    try {
      const result = await api.generateBriefing(watchlistId);
      setBriefing(result);
      refreshTasks();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleReview(signalId: string, status: ReviewStatus, justification: string) {
    if (status === "pending") return;
    await api.reviewSignal(signalId, status, justification);
    setBriefing((prev) =>
      prev
        ? {
            ...prev,
            items: prev.items.map((item) =>
              item.signal.id === signalId
                ? { ...item, signal: { ...item.signal, review_status: status, review_justification: justification } }
                : item,
            ),
          }
        : prev,
    );
  }

  return (
    <div className="pt-24 pb-stack-lg px-container-padding flex-1">
      <div className="mb-stack-lg flex flex-wrap items-end justify-between gap-stack-md">
        <div>
          <h2 className="font-headline-lg text-headline-lg text-on-surface font-bold">
            Executive Briefing
          </h2>
          <p className="text-body-md text-on-surface-variant">
            Resumen por watchlist con revisión humana — HU3. No ejecuta compras ni ventas.
          </p>
        </div>
        <div className="flex items-end gap-stack-sm">
          <div className="flex flex-col gap-1">
            <span className="text-label-sm text-on-surface-variant">Watchlist</span>
            <select
              className="bg-surface-variant border border-outline-variant rounded-lg px-3 py-2 text-label-md font-bold text-on-surface outline-none cursor-pointer"
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
            >
              {watchlists.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          </div>
          <button
            className="px-4 py-2 bg-primary-container text-on-primary-container text-label-md font-bold rounded-lg disabled:opacity-40"
            disabled={!selected || loading}
            onClick={() => generate(selected)}
          >
            {loading ? "Generando…" : "Generar briefing"}
          </button>
        </div>
      </div>

      {error && <div className="mb-stack-md text-body-md text-error">Error: {error}</div>}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-4">
          {!briefing && !loading && (
            <p className="text-body-md text-on-surface-variant">
              Selecciona una watchlist y genera el briefing para ver noticias, movimientos y acciones de
              investigación sugeridas.
            </p>
          )}

          {briefing?.items.map((item) => (
            <div
              key={item.signal.id}
              className="bg-surface-container border border-outline-variant rounded-xl p-5"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-headline-md text-headline-md text-on-surface">
                    {item.instrument}
                  </h3>
                  <p className="text-body-md text-on-surface-variant">{item.news_headline}</p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <ImpactBadge impact={item.signal.impact} />
                  <span className="font-mono-data text-mono-data text-on-surface-variant">
                    {formatPct(item.price_change_pct)}
                  </span>
                </div>
              </div>

              <div className="bg-surface-container-low rounded-lg p-3 mb-3">
                <span className="text-label-sm text-primary uppercase font-bold">Acción de investigación</span>
                <p className="text-body-md text-on-surface mt-1">{item.research_action}</p>
              </div>

              <ul className="space-y-1 mb-4">
                {item.executive_summary.map((line, idx) => (
                  <li key={idx} className="text-body-md text-on-surface-variant flex gap-2">
                    <span className="material-symbols-outlined text-primary text-sm mt-0.5">
                      arrow_right
                    </span>
                    {line}
                  </li>
                ))}
              </ul>

              <ReviewControls
                currentStatus={item.signal.review_status}
                currentJustification={item.signal.review_justification}
                onSave={(status, justification) => handleReview(item.signal.id, status, justification)}
              />
            </div>
          ))}

          {briefing && <Disclaimer text={briefing.disclaimer} />}
        </div>

        <div className="bg-surface-container border border-outline-variant rounded-xl p-5 h-fit">
          <h3 className="font-headline-md text-headline-md text-on-surface mb-3">
            Tareas / Alertas
          </h3>
          <p className="text-label-sm text-on-surface-variant mb-3">
            Nunca son órdenes de compra/venta — solo tareas para revisión humana.
          </p>
          <div className="space-y-2 max-h-[500px] overflow-y-auto custom-scrollbar">
            {tasks.length === 0 && (
              <p className="text-body-md text-on-surface-variant">Sin tareas todavía.</p>
            )}
            {tasks.map((t) => (
              <div
                key={t.id}
                className="bg-surface-container-low border border-outline-variant rounded-lg p-3"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono-data text-[11px] text-primary">{t.instrument}</span>
                  <span className="text-[10px] uppercase text-on-surface-variant">{t.status}</span>
                </div>
                <p className="text-body-md text-on-surface">{t.title}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
