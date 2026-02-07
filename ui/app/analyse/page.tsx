"use client";

import { useMemo, useState, Suspense } from "react";
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
  MessageSquareText,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import { Tabs } from "@/components/ui/tabs";
import { ChartTooltip } from "@/components/ui/chart-tooltip";
import {
  generateStocks,
  generatePriceHistory,
  generateForecast,
  generateRSI,
  generateMACD,
  generateSentimentTimeline,
} from "@/lib/mock-data";
import { formatNumber, formatPercent } from "@/lib/utils";

function AnalyseContent() {
  const searchParams = useSearchParams();
  const paramTicker = searchParams.get("ticker");

  const stocks = useMemo(() => generateStocks(), []);
  const [selectedTicker, setSelectedTicker] = useState(paramTicker ?? stocks[0]?.ticker ?? "BIAT");

  const stock = stocks.find((s) => s.ticker === selectedTicker) ?? stocks[0];
  const priceHistory = useMemo(() => generatePriceHistory(stock.price), [stock.price]);
  const forecast = useMemo(() => generateForecast(priceHistory[priceHistory.length - 1]?.close ?? stock.price), [priceHistory, stock.price]);
  const rsiData = useMemo(() => generateRSI(priceHistory), [priceHistory]);
  const macdData = useMemo(() => generateMACD(priceHistory), [priceHistory]);
  const sentimentTimeline = useMemo(() => generateSentimentTimeline(), []);

  const [chartTab, setChartTab] = useState("price");

  // Combine price history and forecast for overlay chart
  const combinedChart = useMemo(() => {
    const last30 = priceHistory.slice(-30);
    const combined = last30.map((p) => ({
      date: p.date,
      close: p.close,
      predicted: null as number | null,
      upper: null as number | null,
      lower: null as number | null,
    }));
    forecast.forEach((f) => {
      combined.push({
        date: f.date,
        close: null as unknown as number,
        predicted: f.predicted,
        upper: f.upperBound,
        lower: f.lowerBound,
      });
    });
    return combined;
  }, [priceHistory, forecast]);

  const RecommendationIcon = stock.recommendation === "buy" ? ArrowUpRight : stock.recommendation === "sell" ? ArrowDownRight : Minus;
  const recColor = stock.recommendation === "buy" ? "text-success" : stock.recommendation === "sell" ? "text-danger" : "text-warning";
  const recLabel = stock.recommendation === "buy" ? "Acheter" : stock.recommendation === "sell" ? "Vendre" : "Conserver";
  const recBadge = stock.recommendation === "buy" ? "success" : stock.recommendation === "sell" ? "danger" : "warning";

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
          {stocks.map((s) => (
            <option key={s.ticker} value={s.ticker}>
              {s.ticker} — {s.name}
            </option>
          ))}
        </select>
      </PageHeader>

      {/* Stock Header */}
      <Card className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-zinc-800 flex items-center justify-center text-lg font-bold text-foreground">
              {stock.ticker.slice(0, 2)}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">{stock.ticker}</h2>
              <p className="text-sm text-muted">{stock.name} · {stock.sector}</p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-2xl font-semibold text-foreground">{stock.price.toFixed(2)} <span className="text-sm text-muted">TND</span></p>
              <p className={`text-sm font-medium ${stock.change >= 0 ? "text-success" : "text-danger"}`}>
                {formatPercent(stock.change)}
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
              <ComposedChart data={combinedChart}>
                <defs>
                  <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2563eb" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22c55e" stopOpacity={0.15} />
                    <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} axisLine={false} tickLine={false} />
                <YAxis domain={["auto", "auto"]} axisLine={false} tickLine={false} width={50} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="close" stroke="#2563eb" strokeWidth={2} fill="url(#priceGrad)" name="Clôture" connectNulls={false} />
                <Area type="monotone" dataKey="upper" stroke="transparent" fill="url(#forecastGrad)" name="Borne sup." connectNulls={false} />
                <Area type="monotone" dataKey="lower" stroke="transparent" fill="transparent" name="Borne inf." connectNulls={false} />
                <Line type="monotone" dataKey="predicted" stroke="#22c55e" strokeWidth={2} strokeDasharray="6 3" dot={false} name="Prévision" connectNulls={false} />
              </ComposedChart>
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
              <BarChart data={priceHistory.slice(-30)}>
                <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} width={50} />
                <Tooltip content={<ChartTooltip formatter={(v) => formatNumber(v)} />} />
                <Bar dataKey="volume" fill="#3b82f6" opacity={0.6} name="Volume" radius={[2, 2, 0, 0]} />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Info Row */}
      <div className="grid md:grid-cols-3 gap-4 mb-6">
        {/* Forecast Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-muted" />
              Prévision 5 jours
            </CardTitle>
          </CardHeader>
          <div className="space-y-2">
            <div className="grid grid-cols-4 text-[10px] text-muted uppercase tracking-wide pb-1 border-b border-border">
              <span>Date</span>
              <span className="text-right">Prévu</span>
              <span className="text-right">Bas</span>
              <span className="text-right">Haut</span>
            </div>
            {forecast.map((f) => (
              <div key={f.date} className="grid grid-cols-4 text-xs text-foreground">
                <span className="text-muted">{f.date.slice(5)}</span>
                <span className="text-right font-medium">{f.predicted.toFixed(2)}</span>
                <span className="text-right text-danger">{f.lowerBound.toFixed(2)}</span>
                <span className="text-right text-success">{f.upperBound.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Key Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-muted" />
              Statistiques clés
            </CardTitle>
          </CardHeader>
          <div className="space-y-3">
            {[
              ["Prix ouverture", `${priceHistory[priceHistory.length - 1]?.open.toFixed(2)} TND`],
              ["Plus haut (jour)", `${priceHistory[priceHistory.length - 1]?.high.toFixed(2)} TND`],
              ["Plus bas (jour)", `${priceHistory[priceHistory.length - 1]?.low.toFixed(2)} TND`],
              ["Volume", formatNumber(priceHistory[priceHistory.length - 1]?.volume ?? 0)],
              ["Cap. boursière", `${stock.marketCap.toFixed(0)} M TND`],
              ["Secteur", stock.sector],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between text-xs">
                <span className="text-muted">{label}</span>
                <span className="text-foreground font-medium">{value}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Sentiment */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquareText className="w-4 h-4 text-muted" />
              Sentiment
            </CardTitle>
            <Badge
              variant={
                stock.sentiment === "positive" ? "success" : stock.sentiment === "negative" ? "danger" : "muted"
              }
            >
              {stock.sentiment === "positive" ? "Positif" : stock.sentiment === "negative" ? "Négatif" : "Neutre"}
            </Badge>
          </CardHeader>
          <div className="h-[140px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sentimentTimeline.slice(-14)}>
                <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(8)} axisLine={false} tickLine={false} />
                <YAxis domain={[-1, 1]} axisLine={false} tickLine={false} width={25} />
                <Tooltip content={<ChartTooltip />} />
                <ReferenceLine y={0} stroke="#27272a" />
                <Bar
                  dataKey="score"
                  name="Score"
                  radius={[2, 2, 0, 0]}
                  fill="#3b82f6"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-[11px] text-muted mt-2">
            Score moyen : {(sentimentTimeline.reduce((sum, s) => sum + s.score, 0) / sentimentTimeline.length).toFixed(2)} — basé sur {sentimentTimeline.reduce((sum, s) => sum + s.articles, 0)} articles
          </p>
        </Card>
      </div>

      {/* Recommendation Explanation */}
      <Card>
        <CardHeader>
          <CardTitle>Explication de la recommandation</CardTitle>
          <Badge variant={recBadge as "success" | "danger" | "warning"}>{recLabel}</Badge>
        </CardHeader>
        <div className="space-y-3 text-sm text-zinc-300 leading-relaxed">
          <p>
            La recommandation <span className={`font-semibold ${recColor}`}>{recLabel}</span> pour <strong>{stock.ticker}</strong> est
            basée sur l&apos;analyse croisée de plusieurs facteurs :
          </p>
          <ul className="list-disc list-inside space-y-1 text-muted">
            <li>Tendance des prix sur 30 jours : {stock.change >= 0 ? "haussière" : "baissière"} ({formatPercent(stock.change)})</li>
            <li>Sentiment de marché : {stock.sentiment} (score {stock.sentimentScore.toFixed(2)})</li>
            <li>Prévision à 5 jours : {forecast[4]?.predicted > stock.price ? "hausse anticipée" : "baisse anticipée"} vers {forecast[4]?.predicted.toFixed(2)} TND</li>
            <li>Volume : {formatNumber(stock.volume)} titres échangés (séance en cours)</li>
            <li>RSI actuel : {rsiData[rsiData.length - 1]?.rsi.toFixed(1)} — {rsiData[rsiData.length - 1]?.rsi > 70 ? "zone de surachat" : rsiData[rsiData.length - 1]?.rsi < 30 ? "zone de survente" : "zone neutre"}</li>
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
