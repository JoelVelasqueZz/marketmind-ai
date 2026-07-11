import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import ImpactBadge from "../components/ImpactBadge";
import { formatPct, formatPrice } from "../lib/format";
import type { AssetOverview, Watchlist as WatchlistType, WatchlistOverview } from "../types";

function computeSentiment(assets: AssetOverview[]): string {
  const withSignal = assets.filter((a) => a.signal);
  if (withSignal.length === 0) return "Sin datos";
  const counts: Record<string, number> = {};
  for (const a of withSignal) {
    const impact = a.signal!.impact;
    counts[impact] = (counts[impact] ?? 0) + 1;
  }
  const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0];
  return top.charAt(0).toUpperCase() + top.slice(1);
}

function computeTopMover(assets: AssetOverview[]): AssetOverview | null {
  const withChange = assets.filter((a) => a.change_pct_1d !== null);
  if (withChange.length === 0) return null;
  return withChange.reduce((max, a) =>
    Math.abs(a.change_pct_1d!) > Math.abs(max.change_pct_1d!) ? a : max,
  );
}

function computeAvgVolatility(assets: AssetOverview[]): number | null {
  const withChange = assets.filter((a) => a.change_pct_1d !== null);
  if (withChange.length === 0) return null;
  const sum = withChange.reduce((acc, a) => acc + Math.abs(a.change_pct_1d!), 0);
  return sum / withChange.length;
}

export default function Watchlist() {
  const navigate = useNavigate();
  const [watchlists, setWatchlists] = useState<WatchlistType[]>([]);
  const [selected, setSelected] = useState("");
  const [overview, setOverview] = useState<WatchlistOverview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getWatchlists().then((w) => {
      setWatchlists(w);
      if (w[0]) setSelected(w[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    setError(null);
    api
      .getWatchlistOverview(selected)
      .then(setOverview)
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, [selected]);

  const assets = overview?.assets ?? [];
  const sentiment = computeSentiment(assets);
  const topMover = computeTopMover(assets);
  const signalsCount = assets.filter((a) => a.signal).length;
  const avgVolatility = computeAvgVolatility(assets);

  return (
    <div className="pt-24 pb-stack-lg px-container-padding flex-1">
      <div className="mb-stack-lg flex flex-wrap items-end justify-between gap-stack-md">
        <div>
          <h2 className="font-headline-lg text-headline-lg text-on-surface font-bold">
            Active Watchlist
          </h2>
          <p className="text-body-md text-on-surface-variant">
            Monitoreo de {assets.length} instrumentos — extra opcional sobre el alcance mínimo del track.
          </p>
        </div>
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
      </div>

      {error && <div className="mb-stack-md text-body-md text-error">Error: {error}</div>}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-stack-lg">
        <div className="bg-surface-container border border-outline-variant rounded-xl p-4">
          <p className="text-label-sm text-on-surface-variant uppercase font-bold mb-1">
            Sentimiento de cartera
          </p>
          <p className="font-headline-lg text-headline-lg text-on-surface">{sentiment}</p>
        </div>
        <div className="bg-surface-container border border-outline-variant rounded-xl p-4">
          <p className="text-label-sm text-on-surface-variant uppercase font-bold mb-1">Top mover</p>
          <p className="font-headline-lg text-headline-lg text-on-surface">
            {topMover ? `${topMover.symbol} ${formatPct(topMover.change_pct_1d!)}` : "—"}
          </p>
        </div>
        <div className="bg-surface-container border border-outline-variant rounded-xl p-4">
          <p className="text-label-sm text-on-surface-variant uppercase font-bold mb-1">
            Señales generadas
          </p>
          <p className="font-headline-lg text-headline-lg text-on-surface">
            {signalsCount} / {assets.length}
          </p>
        </div>
        <div className="bg-surface-container border border-outline-variant rounded-xl p-4">
          <p className="text-label-sm text-on-surface-variant uppercase font-bold mb-1">
            Volatilidad promedio
          </p>
          <p className="font-headline-lg text-headline-lg text-on-surface">
            {avgVolatility !== null ? `${avgVolatility.toFixed(2)}%` : "—"}
          </p>
        </div>
      </div>

      <div className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-surface-container-high border-b border-outline-variant">
            <tr>
              <th className="px-4 py-3 text-label-sm text-on-surface-variant uppercase">Activo</th>
              <th className="px-4 py-3 text-label-sm text-on-surface-variant uppercase">Precio</th>
              <th className="px-4 py-3 text-label-sm text-on-surface-variant uppercase">Cambio 1d</th>
              <th className="px-4 py-3 text-label-sm text-on-surface-variant uppercase">Señal IA</th>
              <th className="px-4 py-3 text-label-sm text-on-surface-variant uppercase">Confianza</th>
              <th className="px-4 py-3 text-label-sm text-on-surface-variant uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-on-surface-variant">
                  Cargando…
                </td>
              </tr>
            )}
            {!loading &&
              assets.map((a) => (
                <tr key={a.symbol} className="border-b border-outline-variant last:border-0 hover:bg-surface-container-high">
                  <td className="px-4 py-3">
                    <p className="font-bold text-on-surface">{a.symbol}</p>
                    <p className="text-label-sm text-on-surface-variant">{a.name}</p>
                  </td>
                  <td className="px-4 py-3 font-mono-data text-mono-data text-on-surface">
                    {a.price !== null ? `$${formatPrice(a.price)}` : "—"}
                  </td>
                  <td
                    className={`px-4 py-3 font-mono-data text-mono-data ${
                      a.change_pct_1d === null
                        ? "text-on-surface-variant"
                        : a.change_pct_1d >= 0
                          ? "text-success"
                          : "text-error"
                    }`}
                  >
                    {a.change_pct_1d !== null ? formatPct(a.change_pct_1d) : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {a.signal ? <ImpactBadge impact={a.signal.impact} /> : (
                      <span className="text-label-sm text-on-surface-variant">Sin análisis</span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono-data text-mono-data text-on-surface">
                    {a.signal ? `${Math.round(a.signal.confidence * 100)}%` : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      className="px-3 py-1.5 bg-surface-variant hover:bg-surface-container-highest text-on-surface text-label-md font-bold rounded-lg border border-outline-variant"
                      onClick={() => navigate(`/analysis?instrument=${encodeURIComponent(a.symbol)}`)}
                    >
                      Analizar
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
