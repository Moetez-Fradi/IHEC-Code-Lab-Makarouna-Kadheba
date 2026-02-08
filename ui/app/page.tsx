"use client";

import { useEffect, useState, useMemo } from "react";
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
import { useAuth } from "@/lib/auth-context";
import { apiGetOverview, type MarketStock } from "@/lib/api";
import {
  generateAlerts,
  generateNews,
} from "@/lib/mock-data";
import { formatNumber, formatPercent, formatCompact, relativeTime } from "@/lib/utils";
import Link from "next/link";

export default function MarketOverview() {
  const { token } = useAuth();
  const [stocks, setStocks] = useState<MarketStock[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    apiGetOverview(token)
      .then(setStocks)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  const alerts = useMemo(() => generateAlerts(6), []);
  const news = useMemo(() => generateNews(6), []);

  const totalVolume = stocks.reduce((s, x) => s + x.quantiteNegociee, 0);
  const totalCapitaux = stocks.reduce((s, x) => s + x.capitaux, 0);
  const nbUp = stocks.filter((s) => (s.changePercent ?? 0) > 0).length;
  const nbDown = stocks.filter((s) => (s.changePercent ?? 0) < 0).length;
  const globalSentiment = nbUp > nbDown ? "Haussier" : nbDown > nbUp ? "Baissier" : "Neutre";

  const gainers = [...stocks]
    .filter((s) => (s.changePercent ?? 0) > 0)
    .sort((a, b) => (b.changePercent ?? 0) - (a.changePercent ?? 0))
    .slice(0, 5);
  const losers = [...stocks]
    .filter((s) => (s.changePercent ?? 0) < 0)
    .sort((a, b) => (a.changePercent ?? 0) - (b.changePercent ?? 0))
    .slice(0, 5);

  const criticalAlerts = alerts.filter((a) => a.severity === "critical").length;

  // Build a simple TUNINDEX-like line from stocks ordered by session date
  const latestSession = stocks[0]?.seance ?? "";

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-muted">Chargement du marché...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 pb-20 md:pb-6 max-w-[1400px] mx-auto">
      <PageHeader
        title="Vue d'ensemble du marché"
        description="BVMT — Bourse des Valeurs Mobilières de Tunis"
      />

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <StatCard
          label="Valeurs cotées"
          value={String(stocks.length)}
          sub={`Séance ${latestSession}`}
          icon={Activity}
        />
        <StatCard
          label="Tendance"
          value={globalSentiment}
          sub={`${nbUp} hausses · ${nbDown} baisses`}
          icon={BarChart3}
          trend={nbUp > nbDown ? "up" : nbDown > nbUp ? "down" : "neutral"}
        />
        <StatCard
          label="Volume total"
          value={formatCompact(totalVolume)}
          sub={`${formatCompact(totalCapitaux)} TND échangés`}
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

      {/* Market Table + Alerts */}
      <div className="grid lg:grid-cols-3 gap-4 mb-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Marché — Top valeurs par volume</CardTitle>
            <Badge variant="default">{latestSession}</Badge>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-xs text-muted uppercase tracking-wide">
                  <th className="text-left py-2 font-medium">Valeur</th>
                  <th className="text-right py-2 font-medium">Clôture</th>
                  <th className="text-right py-2 font-medium">Var%</th>
                  <th className="text-right py-2 font-medium">Volume</th>
                </tr>
              </thead>
              <tbody>
                {[...stocks]
                  .sort((a, b) => b.quantiteNegociee - a.quantiteNegociee)
                  .slice(0, 10)
                  .map((s) => (
                    <tr key={s.code} className="border-b border-border/50 hover:bg-card-hover transition-colors">
                      <td className="py-2.5">
                        <Link href={`/analyse?ticker=${s.code}`} className="hover:text-accent-light transition-colors">
                          <span className="font-medium text-foreground">{s.code}</span>
                          <span className="text-muted text-xs ml-2 hidden sm:inline">{s.valeur}</span>
                        </Link>
                      </td>
                      <td className="text-right text-foreground font-medium">{s.cloture.toFixed(2)}</td>
                      <td className={`text-right font-medium ${(s.changePercent ?? 0) >= 0 ? "text-success" : "text-danger"}`}>
                        {formatPercent(s.changePercent ?? 0)}
                      </td>
                      <td className="text-right text-muted">{formatCompact(s.quantiteNegociee)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
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
                key={s.code}
                href={`/analyse?ticker=${s.code}`}
                className="flex items-center justify-between py-2 px-2 -mx-2 rounded-lg hover:bg-card-hover transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-9 h-9 rounded-lg bg-zinc-800 flex items-center justify-center text-xs font-semibold text-foreground">
                    {s.code.slice(0, 2)}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-foreground">{s.code}</p>
                    <p className="text-[11px] text-muted truncate max-w-[120px]">{s.valeur}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-foreground">{s.cloture.toFixed(2)}</p>
                  <p className="text-xs text-success font-medium">{formatPercent(s.changePercent ?? 0)}</p>
                </div>
              </Link>
            ))}
            {gainers.length === 0 && <p className="text-xs text-muted py-4 text-center">Aucune hausse</p>}
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
                key={s.code}
                href={`/analyse?ticker=${s.code}`}
                className="flex items-center justify-between py-2 px-2 -mx-2 rounded-lg hover:bg-card-hover transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-9 h-9 rounded-lg bg-zinc-800 flex items-center justify-center text-xs font-semibold text-foreground">
                    {s.code.slice(0, 2)}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-foreground">{s.code}</p>
                    <p className="text-[11px] text-muted truncate max-w-[120px]">{s.valeur}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-foreground">{s.cloture.toFixed(2)}</p>
                  <p className="text-xs text-danger font-medium">{formatPercent(s.changePercent ?? 0)}</p>
                </div>
              </Link>
            ))}
            {losers.length === 0 && <p className="text-xs text-muted py-4 text-center">Aucune baisse</p>}
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
