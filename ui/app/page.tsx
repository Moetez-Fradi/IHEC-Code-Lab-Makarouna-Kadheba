"use client";

import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Newspaper,
  AlertTriangle,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import { ChartTooltip } from "@/components/ui/chart-tooltip";
import {
  generateTunindexHistory,
  generateStocks,
  generateAlerts,
  generateNews,
} from "@/lib/mock-data";
import { formatNumber, formatPercent, formatCompact, relativeTime } from "@/lib/utils";
import Link from "next/link";

export default function MarketOverview() {
  const tunindex = useMemo(() => generateTunindexHistory(), []);
  const stocks = useMemo(() => generateStocks(), []);
  const alerts = useMemo(() => generateAlerts(6), []);
  const news = useMemo(() => generateNews(6), []);

  const lastVal = tunindex[tunindex.length - 1]?.value ?? 0;
  const prevVal = tunindex[tunindex.length - 2]?.value ?? lastVal;
  const tunindexChange = ((lastVal - prevVal) / prevVal) * 100;

  const gainers = [...stocks].sort((a, b) => b.change - a.change).slice(0, 5);
  const losers = [...stocks].sort((a, b) => a.change - b.change).slice(0, 5);

  const sentimentPositive = stocks.filter((s) => s.sentiment === "positive").length;
  const sentimentNeg = stocks.filter((s) => s.sentiment === "negative").length;
  const globalSentiment = sentimentPositive > sentimentNeg ? "Positif" : sentimentNeg > sentimentPositive ? "Négatif" : "Neutre";
  const criticalAlerts = alerts.filter((a) => a.severity === "critical").length;

  return (
    <div className="p-6 pb-20 md:pb-6 max-w-[1400px] mx-auto">
      <PageHeader
        title="Vue d'ensemble du marché"
        description="BVMT — Bourse des Valeurs Mobilières de Tunis"
      />

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <StatCard
          label="TUNINDEX"
          value={formatNumber(lastVal)}
          sub={formatPercent(tunindexChange)}
          icon={Activity}
          trend={tunindexChange >= 0 ? "up" : "down"}
        />
        <StatCard
          label="Sentiment global"
          value={globalSentiment}
          sub={`${sentimentPositive} positifs · ${sentimentNeg} négatifs`}
          icon={BarChart3}
          trend={sentimentPositive > sentimentNeg ? "up" : sentimentNeg > sentimentPositive ? "down" : "neutral"}
        />
        <StatCard
          label="Volume total"
          value={formatCompact(stocks.reduce((s, x) => s + x.volume, 0))}
          sub="Séance en cours"
          icon={TrendingUp}
        />
        <StatCard
          label="Alertes actives"
          value={String(alerts.length)}
          sub={`${criticalAlerts} critique${criticalAlerts > 1 ? "s" : ""}`}
          icon={AlertTriangle}
          trend={criticalAlerts > 0 ? "down" : "neutral"}
        />
      </div>

      {/* TUNINDEX Chart + Alerts */}
      <div className="grid lg:grid-cols-3 gap-4 mb-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>TUNINDEX — 60 derniers jours</CardTitle>
            <Badge variant={tunindexChange >= 0 ? "success" : "danger"}>
              {formatPercent(tunindexChange)}
            </Badge>
          </CardHeader>
          <div className="h-[260px] -mx-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={tunindex}>
                <defs>
                  <linearGradient id="tunGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2563eb" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  tickFormatter={(d: string) => d.slice(5)}
                  tick={{ fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  domain={["auto", "auto"]}
                  tick={{ fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  width={50}
                />
                <Tooltip content={<ChartTooltip formatter={(v) => formatNumber(v)} />} />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#2563eb"
                  strokeWidth={2}
                  fill="url(#tunGrad)"
                  name="TUNINDEX"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Alertes récentes</CardTitle>
            <Link href="/surveillance" className="text-xs text-accent-light hover:underline">
              Tout voir
            </Link>
          </CardHeader>
          <div className="space-y-3">
            {alerts.slice(0, 5).map((a) => (
              <div key={a.id} className="flex gap-3 items-start">
                <div
                  className={`mt-1 w-2 h-2 rounded-full shrink-0 ${
                    a.severity === "critical"
                      ? "bg-danger"
                      : a.severity === "warning"
                      ? "bg-warning"
                      : "bg-accent-light"
                  }`}
                />
                <div className="min-w-0">
                  <p className="text-xs text-foreground font-medium truncate">{a.title}</p>
                  <p className="text-[11px] text-muted truncate">{a.ticker} — {relativeTime(a.timestamp)}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Gainers / Losers */}
      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Top Gagnants</CardTitle>
            <TrendingUp className="w-4 h-4 text-success" />
          </CardHeader>
          <div className="space-y-2">
            {gainers.map((s) => (
              <Link
                key={s.ticker}
                href={`/analyse?ticker=${s.ticker}`}
                className="flex items-center justify-between py-2 px-2 -mx-2 rounded-lg hover:bg-card-hover transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-9 h-9 rounded-lg bg-zinc-800 flex items-center justify-center text-xs font-semibold text-foreground">
                    {s.ticker.slice(0, 2)}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-foreground">{s.ticker}</p>
                    <p className="text-[11px] text-muted">{s.sector}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-foreground">{s.price.toFixed(2)}</p>
                  <p className="text-xs text-success font-medium">{formatPercent(s.change)}</p>
                </div>
              </Link>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Perdants</CardTitle>
            <TrendingDown className="w-4 h-4 text-danger" />
          </CardHeader>
          <div className="space-y-2">
            {losers.map((s) => (
              <Link
                key={s.ticker}
                href={`/analyse?ticker=${s.ticker}`}
                className="flex items-center justify-between py-2 px-2 -mx-2 rounded-lg hover:bg-card-hover transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-9 h-9 rounded-lg bg-zinc-800 flex items-center justify-center text-xs font-semibold text-foreground">
                    {s.ticker.slice(0, 2)}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-foreground">{s.ticker}</p>
                    <p className="text-[11px] text-muted">{s.sector}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-foreground">{s.price.toFixed(2)}</p>
                  <p className="text-xs text-danger font-medium">{formatPercent(s.change)}</p>
                </div>
              </Link>
            ))}
          </div>
        </Card>
      </div>

      {/* News Feed */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Newspaper className="w-4 h-4 text-muted" />
            Actualités
          </CardTitle>
        </CardHeader>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {news.map((n) => (
            <div
              key={n.id}
              className="p-3 rounded-lg border border-border hover:border-zinc-600 transition-colors"
            >
              <div className="flex items-center gap-2 mb-2">
                <Badge
                  variant={
                    n.sentiment === "positive"
                      ? "success"
                      : n.sentiment === "negative"
                      ? "danger"
                      : "muted"
                  }
                >
                  {n.sentiment === "positive" ? "Positif" : n.sentiment === "negative" ? "Négatif" : "Neutre"}
                </Badge>
                {n.tickers.length > 0 && (
                  <span className="text-[10px] text-muted font-mono">{n.tickers.join(", ")}</span>
                )}
              </div>
              <p className="text-sm font-medium text-foreground leading-snug mb-1">{n.title}</p>
              <p className="text-[11px] text-muted">
                {n.source} · {relativeTime(n.date)}
              </p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
