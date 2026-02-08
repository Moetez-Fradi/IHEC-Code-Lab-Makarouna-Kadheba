"use client";

import { useEffect, useMemo, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ComposedChart,
} from "recharts";
import {
  TrendingUp,
  Activity,
  Droplets,
  Target,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import { StatCard } from "@/components/ui/stat-card";
import { ChartTooltip } from "@/components/ui/chart-tooltip";
import { useAuth } from "@/lib/auth-context";
import {
  apiGetStocks,
  apiGetForecast,
  type ForecastReport,
} from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/utils";

function ForecastContent() {
  const searchParams = useSearchParams();
  const paramTicker = searchParams.get("ticker");
  const { token } = useAuth();

  const [stockList, setStockList] = useState<{ code: string; valeur: string }[]>([]);
  const [selectedTicker, setSelectedTicker] = useState(paramTicker ?? "");
  const [forecast, setForecast] = useState<ForecastReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load stock list
  useEffect(() => {
    if (!token) return;
    apiGetStocks(token)
      .then((list) => {
        setStockList(list);
        if (!selectedTicker && list.length > 0) setSelectedTicker(paramTicker ?? list[0].code);
      })
      .catch(console.error);
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load forecast when ticker changes
  useEffect(() => {
    if (!token || !selectedTicker) return;
    setLoading(true);
    setError(null);
    setForecast(null);
    apiGetForecast(token, selectedTicker)
      .then(setForecast)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [token, selectedTicker]);

  // ── Chart data ──
  const chartData = useMemo(() => {
    if (!forecast) return [];

    const historical = forecast.historical_close.map((h) => ({
      date: h.date,
      close: h.close,
      type: "historical" as const,
    }));

    const predictions = forecast.daily_forecasts.map((f) => ({
      date: f.date,
      predicted: f.predicted_close,
      confidence_low: f.confidence_low,
      confidence_high: f.confidence_high,
      type: "forecast" as const,
    }));

    // Bridge: add last historical point as first prediction point
    const lastHist = historical[historical.length - 1];
    const bridge = lastHist
      ? { ...lastHist, predicted: lastHist.close, confidence_low: lastHist.close, confidence_high: lastHist.close, type: "bridge" as const }
      : null;

    return [...historical, ...(bridge ? [bridge] : []), ...predictions];
  }, [forecast]);

  const volumeChartData = useMemo(() => {
    if (!forecast) return [];
    return forecast.daily_forecasts.map((f) => ({
      date: f.date,
      volume: f.predicted_volume,
      liquidity: f.liquidity_probability,
      label: f.liquidity_label,
    }));
  }, [forecast]);

  const stockInfo = stockList.find((s) => s.code === selectedTicker);

  // ── Metrics summary ──
  const avgDA = useMemo(() => {
    if (!forecast) return 0;
    const values = Object.values(forecast.metrics).map((m) => m.directional_accuracy);
    return values.reduce((a, b) => a + b, 0) / values.length;
  }, [forecast]);

  const avgMAPE = useMemo(() => {
    if (!forecast) return 0;
    const values = Object.values(forecast.metrics).map((m) => m.mape);
    return values.reduce((a, b) => a + b, 0) / values.length;
  }, [forecast]);

  // ── Render ──

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-accent animate-spin" />
          <span className="text-sm text-muted">Entraînement du modèle et calcul des prévisions...</span>
          <span className="text-xs text-zinc-600">Cela peut prendre quelques secondes</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 pb-20 md:pb-6 max-w-[1400px] mx-auto">
      <PageHeader
        title="Prévision"
        description="Prédiction du prix de clôture, volume et liquidité pour les 5 prochains jours"
      >
        <select
          value={selectedTicker}
          onChange={(e) => setSelectedTicker(e.target.value)}
          className="bg-zinc-900 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
        >
          {stockList.map((s) => (
            <option key={s.code} value={s.code}>
              {s.code} — {s.valeur}
            </option>
          ))}
        </select>
      </PageHeader>

      {error && (
        <Card className="mb-6 border-danger/30">
          <div className="flex items-center gap-3 text-danger">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <div>
              <p className="text-sm font-medium">Erreur de prévision</p>
              <p className="text-xs text-zinc-400 mt-1">{error}</p>
            </div>
          </div>
        </Card>
      )}

      {forecast && (
        <>
          {/* Stock Header */}
          <Card className="mb-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent/20 to-accent/5 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-accent" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-foreground">{forecast.stock_name}</h2>
                  <p className="text-xs text-muted">{forecast.stock_code} · Modèle : {forecast.model}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-xs text-muted">Prévision depuis</p>
                  <p className="text-sm font-medium text-foreground">{forecast.forecast_from}</p>
                </div>
                <Badge variant="info">{forecast.horizon} jours</Badge>
              </div>
            </div>
          </Card>

          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard
              label="Prix prévu J+1"
              value={`${forecast.daily_forecasts[0].predicted_close.toFixed(3)} TND`}
              sub={`IC: [${forecast.daily_forecasts[0].confidence_low.toFixed(2)}, ${forecast.daily_forecasts[0].confidence_high.toFixed(2)}]`}
              icon={Target}
            />
            <StatCard
              label="Prix prévu J+5"
              value={`${forecast.daily_forecasts[4].predicted_close.toFixed(3)} TND`}
              sub={`IC: [${forecast.daily_forecasts[4].confidence_low.toFixed(2)}, ${forecast.daily_forecasts[4].confidence_high.toFixed(2)}]`}
              icon={TrendingUp}
            />
            <StatCard
              label="Précision directionnelle"
              value={`${avgDA.toFixed(1)}%`}
              sub="Moyenne sur 5 horizons"
              icon={Activity}
              trend={avgDA > 55 ? "up" : avgDA < 45 ? "down" : "neutral"}
            />
            <StatCard
              label="MAPE moyen"
              value={`${avgMAPE.toFixed(2)}%`}
              sub="Erreur relative moyenne"
              icon={Target}
              trend={avgMAPE < 3 ? "up" : avgMAPE > 5 ? "down" : "neutral"}
            />
          </div>

          {/* Main Price Chart */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-accent" />
                Historique + Prévision sur 5 jours
              </CardTitle>
            </CardHeader>
            <div className="h-[350px]">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <defs>
                    <linearGradient id="histGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#2563eb" stopOpacity={0.15} />
                      <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.15} />
                      <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="date"
                    tickFormatter={(d: string) => d.slice(5)}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis domain={["auto", "auto"]} axisLine={false} tickLine={false} width={55} tick={{ fontSize: 11 }} />
                  <Tooltip content={<ChartTooltip />} />
                  <ReferenceLine
                    x={forecast.forecast_from}
                    stroke="#525252"
                    strokeDasharray="4 4"
                    label={{ value: "Aujourd'hui", fill: "#a1a1aa", fontSize: 10 }}
                  />
                  {/* Confidence interval band */}
                  <Area
                    type="monotone"
                    dataKey="confidence_high"
                    stroke="none"
                    fill="url(#forecastGrad)"
                    name="IC Haut"
                    connectNulls={false}
                  />
                  <Area
                    type="monotone"
                    dataKey="confidence_low"
                    stroke="none"
                    fill="#18181b"
                    name="IC Bas"
                    connectNulls={false}
                  />
                  {/* Historical price */}
                  <Area
                    type="monotone"
                    dataKey="close"
                    stroke="#2563eb"
                    strokeWidth={2}
                    fill="url(#histGrad)"
                    name="Clôture (réel)"
                    connectNulls={false}
                  />
                  {/* Forecast line */}
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    strokeDasharray="6 3"
                    dot={{ r: 4, fill: "#f59e0b", stroke: "#18181b", strokeWidth: 2 }}
                    name="Prévu"
                    connectNulls={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Volume + Liquidity Row */}
          <div className="grid md:grid-cols-2 gap-4 mb-6">
            {/* Volume Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-muted" />
                  Volume prévu (5 jours)
                </CardTitle>
              </CardHeader>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={volumeChartData}>
                    <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} axisLine={false} tickLine={false} />
                    <YAxis axisLine={false} tickLine={false} width={50} tick={{ fontSize: 11 }} />
                    <Tooltip content={<ChartTooltip formatter={(v) => formatNumber(v)} />} />
                    <Bar dataKey="volume" fill="#3b82f6" opacity={0.7} name="Volume" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Liquidity Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Droplets className="w-4 h-4 text-muted" />
                  Probabilité de liquidité élevée
                </CardTitle>
              </CardHeader>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={volumeChartData}>
                    <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 1]} axisLine={false} tickLine={false} width={40} tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 11 }} />
                    <Tooltip content={<ChartTooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />} />
                    <ReferenceLine y={0.5} stroke="#525252" strokeDasharray="3 3" />
                    <Bar
                      dataKey="liquidity"
                      name="Prob. Liquidité"
                      radius={[4, 4, 0, 0]}
                      fill="#10b981"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          {/* Forecast Table */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Prévisions détaillées</CardTitle>
            </CardHeader>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-[11px] text-muted uppercase tracking-wide">
                    <th className="text-left py-2 pr-4">Date</th>
                    <th className="text-right py-2 px-3">Prix Clôture</th>
                    <th className="text-right py-2 px-3">IC Bas</th>
                    <th className="text-right py-2 px-3">IC Haut</th>
                    <th className="text-right py-2 px-3">Volume</th>
                    <th className="text-right py-2 px-3">Prob. Liquidité</th>
                    <th className="text-center py-2 pl-3">Liquidité</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast.daily_forecasts.map((f, i) => (
                    <tr key={f.date} className="border-b border-border/50 hover:bg-card-hover transition-colors">
                      <td className="py-2.5 pr-4 font-medium text-foreground">{f.date}</td>
                      <td className="py-2.5 px-3 text-right font-semibold text-foreground">{f.predicted_close.toFixed(3)} TND</td>
                      <td className="py-2.5 px-3 text-right text-muted">{f.confidence_low.toFixed(3)}</td>
                      <td className="py-2.5 px-3 text-right text-muted">{f.confidence_high.toFixed(3)}</td>
                      <td className="py-2.5 px-3 text-right text-foreground">{formatNumber(f.predicted_volume)}</td>
                      <td className="py-2.5 px-3 text-right text-foreground">{(f.liquidity_probability * 100).toFixed(1)}%</td>
                      <td className="py-2.5 pl-3 text-center">
                        <Badge variant={f.liquidity_label === "high" ? "success" : "danger"}>
                          {f.liquidity_label === "high" ? "Élevée" : "Faible"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Metrics Table */}
          <Card>
            <CardHeader>
              <CardTitle>Métriques du modèle (validation)</CardTitle>
            </CardHeader>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-[11px] text-muted uppercase tracking-wide">
                    <th className="text-left py-2 pr-4">Horizon</th>
                    <th className="text-right py-2 px-3">RMSE</th>
                    <th className="text-right py-2 px-3">MAE</th>
                    <th className="text-right py-2 px-3">MAPE (%)</th>
                    <th className="text-right py-2 pl-3">Dir. Accuracy (%)</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(forecast.metrics).map(([horizon, m]) => (
                    <tr key={horizon} className="border-b border-border/50">
                      <td className="py-2.5 pr-4 font-medium text-foreground">{horizon}</td>
                      <td className="py-2.5 px-3 text-right text-foreground">{m.rmse.toFixed(4)}</td>
                      <td className="py-2.5 px-3 text-right text-foreground">{m.mae.toFixed(4)}</td>
                      <td className="py-2.5 px-3 text-right text-foreground">{m.mape.toFixed(2)}%</td>
                      <td className="py-2.5 pl-3 text-right">
                        <span className={m.directional_accuracy >= 55 ? "text-success" : m.directional_accuracy < 45 ? "text-danger" : "text-warning"}>
                          {m.directional_accuracy.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-[11px] text-zinc-500 mt-4 pt-3 border-t border-border">
              RMSE = Root Mean Square Error · MAE = Mean Absolute Error · MAPE = Mean Absolute Percentage Error · Dir. Accuracy = fraction des directions correctement prédites.
              Le modèle est entraîné à la volée sur les données historiques du titre sélectionné.
            </p>
          </Card>
        </>
      )}
    </div>
  );
}

export default function PrevisionPage() {
  return (
    <Suspense fallback={<div className="p-6 text-muted">Chargement...</div>}>
      <ForecastContent />
    </Suspense>
  );
}
