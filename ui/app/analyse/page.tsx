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
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  TrendingUp,
  BarChart3,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import { Tabs } from "@/components/ui/tabs";
import { ChartTooltip } from "@/components/ui/chart-tooltip";
import { useAuth } from "@/lib/auth-context";
import { apiGetStocks, apiGetHistory, type MarketStock } from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/utils";

function computeRSI(history: MarketStock[], period = 14) {
  const closes = history.map((h) => h.cloture);
  const rsi: { date: string; rsi: number }[] = [];
  for (let i = period; i < closes.length; i++) {
    let gains = 0, losses = 0;
    for (let j = i - period + 1; j <= i; j++) {
      const diff = closes[j] - closes[j - 1];
      if (diff > 0) gains += diff; else losses -= diff;
    }
    const avgGain = gains / period;
    const avgLoss = losses / period;
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    rsi.push({ date: history[i].seance, rsi: 100 - 100 / (1 + rs) });
  }
  return rsi;
}

function computeMACD(history: MarketStock[]) {
  const closes = history.map((h) => h.cloture);
  const ema = (data: number[], period: number) => {
    const k = 2 / (period + 1);
    const result = [data[0]];
    for (let i = 1; i < data.length; i++) result.push(data[i] * k + result[i - 1] * (1 - k));
    return result;
  };
  const ema12 = ema(closes, 12);
  const ema26 = ema(closes, 26);
  const macdLine = ema12.map((v, i) => v - ema26[i]);
  const signalLine = ema(macdLine, 9);
  return history.slice(26).map((h, i) => ({
    date: h.seance,
    macd: macdLine[i + 26],
    signal: signalLine[i + 26],
    histogram: macdLine[i + 26] - signalLine[i + 26],
  }));
}

function AnalyseContent() {
  const searchParams = useSearchParams();
  const paramTicker = searchParams.get("ticker");
  const { token } = useAuth();

  const [stockList, setStockList] = useState<{ code: string; valeur: string }[]>([]);
  const [selectedTicker, setSelectedTicker] = useState(paramTicker ?? "");
  const [history, setHistory] = useState<MarketStock[]>([]);
  const [loading, setLoading] = useState(true);

  // Load stock list
  useEffect(() => {
    if (!token) return;
    apiGetStocks(token).then((list) => {
      setStockList(list);
      if (!selectedTicker && list.length > 0) setSelectedTicker(paramTicker ?? list[0].code);
    }).catch(console.error);
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load history when ticker changes
  useEffect(() => {
    if (!token || !selectedTicker) return;
    setLoading(true);
    apiGetHistory(token, selectedTicker, 120)
      .then(setHistory)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token, selectedTicker]);

  const [chartTab, setChartTab] = useState("price");

  const latest = history[history.length - 1];
  const prevSession = history.length > 1 ? history[history.length - 2] : null;
  const changePercent = latest && prevSession ? ((latest.cloture - prevSession.cloture) / prevSession.cloture) * 100 : 0;

  const rsiData = useMemo(() => computeRSI(history), [history]);
  const macdData = useMemo(() => computeMACD(history), [history]);

  // Simple chart data
  const chartData = useMemo(() => history.map((h) => ({
    date: h.seance,
    close: h.cloture,
    open: h.ouverture,
    high: h.plusHaut,
    low: h.plusBas,
    volume: h.quantiteNegociee,
  })), [history]);

  const stockInfo = stockList.find((s) => s.code === selectedTicker);
  const recDirection = changePercent > 1 ? "buy" : changePercent < -1 ? "sell" : "hold";
  const RecommendationIcon = recDirection === "buy" ? ArrowUpRight : recDirection === "sell" ? ArrowDownRight : Minus;
  const recColor = recDirection === "buy" ? "text-success" : recDirection === "sell" ? "text-danger" : "text-warning";
  const recLabel = recDirection === "buy" ? "Acheter" : recDirection === "sell" ? "Vendre" : "Conserver";
  const recBadge = recDirection === "buy" ? "success" : recDirection === "sell" ? "danger" : "warning";

  if (loading && history.length === 0) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-muted">Chargement des données...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 pb-20 md:pb-6 max-w-[1400px] mx-auto">
      <PageHeader
        title="Analyse de valeur"
        description="Historique, prévisions, indicateurs techniques et sentiment"
      >
        {/* Ticker Selector */}
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

      {/* Stock Header */}
      <Card className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-zinc-800 flex items-center justify-center text-lg font-bold text-foreground">
              {selectedTicker.slice(0, 2)}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">{selectedTicker}</h2>
              <p className="text-sm text-muted">{stockInfo?.valeur ?? selectedTicker}</p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-2xl font-semibold text-foreground">{latest?.cloture.toFixed(2) ?? "—"} <span className="text-sm text-muted">TND</span></p>
              <p className={`text-sm font-medium ${changePercent >= 0 ? "text-success" : "text-danger"}`}>
                {formatPercent(changePercent)}
              </p>
            </div>
            <div className="flex flex-col items-center gap-1 pl-6 border-l border-border">
              <RecommendationIcon className={`w-6 h-6 ${recColor}`} />
              <Badge variant={recBadge as "success" | "danger" | "warning"}>{recLabel}</Badge>
            </div>
          </div>
        </div>
      </Card>

      {/* Chart Tabs */}
      <div className="mb-4">
        <Tabs
          tabs={[
            { id: "price", label: "Prix + Prévision" },
            { id: "rsi", label: "RSI" },
            { id: "macd", label: "MACD" },
            { id: "volume", label: "Volume" },
          ]}
          defaultTab="price"
          onChange={setChartTab}
        />
      </div>

      {/* Main Chart */}
      <Card className="mb-6">
        <div className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            {chartTab === "price" ? (
              <AreaChart data={chartData.slice(-60)}>
                <defs>
                  <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2563eb" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(3, 8)} axisLine={false} tickLine={false} />
                <YAxis domain={["auto", "auto"]} axisLine={false} tickLine={false} width={50} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="close" stroke="#2563eb" strokeWidth={2} fill="url(#priceGrad)" name="Clôture" />
              </AreaChart>
            ) : chartTab === "rsi" ? (
              <LineChart data={rsiData}>
                <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} axisLine={false} tickLine={false} width={35} />
                <Tooltip content={<ChartTooltip />} />
                <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" label={{ value: "Suracheté", fill: "#ef4444", fontSize: 10 }} />
                <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="3 3" label={{ value: "Survendu", fill: "#22c55e", fontSize: 10 }} />
                <Line type="monotone" dataKey="rsi" stroke="#f59e0b" strokeWidth={1.5} dot={false} name="RSI" />
              </LineChart>
            ) : chartTab === "macd" ? (
              <ComposedChart data={macdData}>
                <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} axisLine={false} tickLine={false} />
                <YAxis domain={["auto", "auto"]} axisLine={false} tickLine={false} width={35} />
                <Tooltip content={<ChartTooltip />} />
                <ReferenceLine y={0} stroke="#27272a" />
                <Bar dataKey="histogram" name="Histogramme" fill="#3b82f6" opacity={0.5} />
                <Line type="monotone" dataKey="macd" stroke="#2563eb" strokeWidth={1.5} dot={false} name="MACD" />
                <Line type="monotone" dataKey="signal" stroke="#ef4444" strokeWidth={1.5} dot={false} name="Signal" />
              </ComposedChart>
            ) : (
              <BarChart data={chartData.slice(-30)}>
                <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(3, 8)} axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} width={50} />
                <Tooltip content={<ChartTooltip formatter={(v) => formatNumber(v)} />} />
                <Bar dataKey="volume" fill="#3b82f6" opacity={0.6} name="Volume" radius={[2, 2, 0, 0]} />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Info Row */}
      <div className="grid md:grid-cols-2 gap-4 mb-6">
        {/* Key Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-muted" />
              Statistiques clés
            </CardTitle>
          </CardHeader>
          <div className="space-y-3">
            {latest && [
              ["Ouverture", `${latest.ouverture.toFixed(2)} TND`],
              ["Clôture", `${latest.cloture.toFixed(2)} TND`],
              ["Plus haut", `${latest.plusHaut.toFixed(2)} TND`],
              ["Plus bas", `${latest.plusBas.toFixed(2)} TND`],
              ["Quantité négociée", formatNumber(latest.quantiteNegociee)],
              ["Capitaux", `${formatNumber(latest.capitaux)} TND`],
              ["Transactions", formatNumber(latest.nbTransaction)],
              ["Séance", latest.seance],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between text-xs">
                <span className="text-muted">{label}</span>
                <span className="text-foreground font-medium">{value}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Price History Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-muted" />
              Dernières séances
            </CardTitle>
          </CardHeader>
          <div className="space-y-2">
            <div className="grid grid-cols-5 text-[10px] text-muted uppercase tracking-wide pb-1 border-b border-border">
              <span>Date</span>
              <span className="text-right">Ouv.</span>
              <span className="text-right">Clôt.</span>
              <span className="text-right">Haut</span>
              <span className="text-right">Vol.</span>
            </div>
            {history.slice(-7).reverse().map((h) => (
              <div key={h.seance} className="grid grid-cols-5 text-xs text-foreground">
                <span className="text-muted">{h.seance.slice(0, 5)}</span>
                <span className="text-right">{h.ouverture.toFixed(2)}</span>
                <span className="text-right font-medium">{h.cloture.toFixed(2)}</span>
                <span className="text-right">{h.plusHaut.toFixed(2)}</span>
                <span className="text-right text-muted">{formatNumber(h.quantiteNegociee)}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recommendation Explanation */}
      <Card>
        <CardHeader>
          <CardTitle>Analyse technique</CardTitle>
          <Badge variant={recBadge as "success" | "danger" | "warning"}>{recLabel}</Badge>
        </CardHeader>
        <div className="space-y-3 text-sm text-zinc-300 leading-relaxed">
          <p>
            La recommandation <span className={`font-semibold ${recColor}`}>{recLabel}</span> pour <strong>{selectedTicker}</strong> est
            basée sur l&apos;analyse croisée de plusieurs facteurs :
          </p>
          <ul className="list-disc list-inside space-y-1 text-muted">
            <li>Tendance des prix : {changePercent >= 0 ? "haussière" : "baissière"} ({formatPercent(changePercent)})</li>
            <li>Volume dernière séance : {formatNumber(latest?.quantiteNegociee ?? 0)} titres échangés</li>
            <li>RSI actuel : {rsiData.length > 0 ? rsiData[rsiData.length - 1].rsi.toFixed(1) : "N/A"} — {rsiData.length > 0 ? (rsiData[rsiData.length - 1].rsi > 70 ? "zone de surachat" : rsiData[rsiData.length - 1].rsi < 30 ? "zone de survente" : "zone neutre") : ""}</li>
            <li>Nombre de séances analysées : {history.length}</li>
          </ul>
          <p className="text-xs text-zinc-500 pt-2 border-t border-border">
            Cette analyse est fournie à titre informatif uniquement et ne constitue pas un conseil en investissement. Les performances passées ne garantissent pas les résultats futurs.
          </p>
        </div>
      </Card>
    </div>
  );
}

export default function AnalysePage() {
  return (
    <Suspense fallback={<div className="p-6 text-muted">Chargement...</div>}>
      <AnalyseContent />
    </Suspense>
  );
}