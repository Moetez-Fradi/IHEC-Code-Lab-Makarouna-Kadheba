"use client";

import { useMemo, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import {
  Wallet,
  TrendingUp,
  Shield,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import { ChartTooltip } from "@/components/ui/chart-tooltip";
import { generatePortfolio, generateStocks } from "@/lib/mock-data";
import { formatCurrency, formatPercent, formatNumber, cn } from "@/lib/utils";
import Link from "next/link";

const PIE_COLORS = ["#2563eb", "#7c3aed", "#06b6d4", "#22c55e", "#f59e0b", "#ef4444", "#ec4899", "#8b5cf6", "#14b8a6", "#f97316"];

export default function PortfolioPage() {
  const portfolio = useMemo(() => generatePortfolio(), []);
  const stocks = useMemo(() => generateStocks(), []);
  const [capitalInput, setCapitalInput] = useState("5000");

  // Sector allocation
  const sectorMap = new Map<string, number>();
  portfolio.positions.forEach((p) => {
    const existing = sectorMap.get(p.sector) ?? 0;
    sectorMap.set(p.sector, existing + p.weight);
  });
  const sectorData = Array.from(sectorMap.entries()).map(([name, value]) => ({ name, value: Math.round(value * 100) / 100 }));

  // Performance chart (simulated monthly)
  const perfChart = useMemo(() => {
    const months = ["Sep", "Oct", "Nov", "Déc", "Jan", "Fév"];
    let val = portfolio.totalCost;
    return months.map((m) => {
      val += val * (Math.random() * 0.08 - 0.03);
      return { month: m, value: Math.round(val * 100) / 100 };
    });
  }, [portfolio.totalCost]);

  const profileLabels: Record<string, string> = {
    conservateur: "Conservateur",
    modéré: "Modéré",
    agressif: "Agressif",
  };
  const profileColors: Record<string, string> = {
    conservateur: "success",
    modéré: "warning",
    agressif: "danger",
  };

  // Suggestions based on risk profile
  const suggestions = useMemo(() => {
    const recs = stocks.filter((s) => s.recommendation === "buy").slice(0, 3);
    return recs;
  }, [stocks]);

  return (
    <div className="p-6 pb-20 md:pb-6 max-w-[1400px] mx-auto">
      <PageHeader
        title="Mon portefeuille"
        description="Simulation · Positions, performance et suggestions"
      >
        <Badge variant={profileColors[portfolio.riskProfile] as "success" | "warning" | "danger"}>
          Profil {profileLabels[portfolio.riskProfile]}
        </Badge>
      </PageHeader>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <StatCard
          label="Valeur totale"
          value={formatCurrency(portfolio.totalValue)}
          icon={Wallet}
        />
        <StatCard
          label="P&L"
          value={formatCurrency(portfolio.pnl)}
          sub={formatPercent(portfolio.pnlPercent)}
          icon={TrendingUp}
          trend={portfolio.pnl >= 0 ? "up" : "down"}
        />
        <StatCard
          label="Ratio de Sharpe"
          value={portfolio.sharpe.toFixed(2)}
          sub="Rendement ajusté au risque"
          icon={BarChart3}
        />
        <StatCard
          label="Max Drawdown"
          value={`${portfolio.maxDrawdown.toFixed(1)}%`}
          sub="Perte max depuis le pic"
          icon={Shield}
          trend="down"
        />
      </div>

      {/* Performance + Allocation */}
      <div className="grid lg:grid-cols-3 gap-4 mb-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Performance du portefeuille</CardTitle>
          </CardHeader>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={perfChart}>
                <defs>
                  <linearGradient id="perfGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22c55e" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" axisLine={false} tickLine={false} />
                <YAxis domain={["auto", "auto"]} axisLine={false} tickLine={false} width={60} tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}K`} />
                <Tooltip content={<ChartTooltip formatter={(v) => formatCurrency(v)} />} />
                <Area type="monotone" dataKey="value" stroke="#22c55e" strokeWidth={2} fill="url(#perfGrad)" name="Valeur" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Répartition sectorielle</CardTitle>
          </CardHeader>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sectorData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                  nameKey="name"
                >
                  {sectorData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  content={<ChartTooltip formatter={(v) => `${v.toFixed(1)}%`} />}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            {sectorData.map((s, i) => (
              <div key={s.name} className="flex items-center gap-1.5 text-[11px] text-muted">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                {s.name}
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Positions Table */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Positions</CardTitle>
          <span className="text-xs text-muted">{portfolio.positions.length} lignes</span>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-xs text-muted uppercase tracking-wide">
                <th className="text-left py-2 font-medium">Valeur</th>
                <th className="text-right py-2 font-medium">Qté</th>
                <th className="text-right py-2 font-medium">PRU</th>
                <th className="text-right py-2 font-medium">Cours</th>
                <th className="text-right py-2 font-medium">P&L</th>
                <th className="text-right py-2 font-medium">Poids</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.positions.map((p) => (
                <tr key={p.ticker} className="border-b border-border/50 hover:bg-card-hover transition-colors">
                  <td className="py-3">
                    <Link href={`/analyse?ticker=${p.ticker}`} className="hover:text-accent-light transition-colors">
                      <span className="font-medium text-foreground">{p.ticker}</span>
                      <span className="text-muted text-xs ml-2">{p.sector}</span>
                    </Link>
                  </td>
                  <td className="text-right text-foreground">{p.shares}</td>
                  <td className="text-right text-muted">{p.avgCost.toFixed(2)}</td>
                  <td className="text-right text-foreground font-medium">{p.currentPrice.toFixed(2)}</td>
                  <td className={cn("text-right font-medium", p.pnl >= 0 ? "text-success" : "text-danger")}>
                    {p.pnl >= 0 ? "+" : ""}{p.pnl.toFixed(2)}
                    <span className="text-xs ml-1">({formatPercent(p.pnlPercent)})</span>
                  </td>
                  <td className="text-right text-muted">{p.weight.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Investment Suggestion + Simulator */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Suggestions */}
        <Card>
          <CardHeader>
            <CardTitle>Suggestions d&apos;investissement</CardTitle>
          </CardHeader>
          <div className="space-y-3">
            {suggestions.map((s) => (
              <Link
                key={s.ticker}
                href={`/analyse?ticker=${s.ticker}`}
                className="flex items-center justify-between p-3 rounded-lg border border-border hover:border-zinc-600 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-success/10 flex items-center justify-center">
                    <ArrowUpRight className="w-4 h-4 text-success" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{s.ticker}</p>
                    <p className="text-[11px] text-muted">{s.sector} · Sentiment {s.sentiment}</p>
                  </div>
                </div>
                <Badge variant="success">Acheter</Badge>
              </Link>
            ))}
          </div>
        </Card>

        {/* Capital Simulator */}
        <Card>
          <CardHeader>
            <CardTitle>Simulateur de capital</CardTitle>
          </CardHeader>
          <p className="text-sm text-muted mb-4">
            &quot;Je veux investir X TND, que recommandez-vous ?&quot;
          </p>
          <div className="flex gap-2 mb-4">
            <input
              type="number"
              value={capitalInput}
              onChange={(e) => setCapitalInput(e.target.value)}
              className="flex-1 bg-zinc-900 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
              placeholder="Montant en TND"
            />
            <span className="flex items-center text-sm text-muted">TND</span>
          </div>
          {(() => {
            const capital = Number(capitalInput) || 0;
            if (capital <= 0) return <p className="text-xs text-muted">Saisissez un montant pour voir la répartition suggérée.</p>;
            const alloc = suggestions.map((s, i) => ({
              ticker: s.ticker,
              percent: i === 0 ? 40 : i === 1 ? 35 : 25,
            }));
            return (
              <div className="space-y-2">
                {alloc.map((a) => (
                  <div key={a.ticker} className="flex items-center justify-between text-sm">
                    <span className="text-foreground font-medium">{a.ticker}</span>
                    <div className="flex items-center gap-3">
                      <div className="w-24 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                        <div className="h-full bg-accent rounded-full" style={{ width: `${a.percent}%` }} />
                      </div>
                      <span className="text-muted text-xs w-8 text-right">{a.percent}%</span>
                      <span className="text-foreground font-medium w-20 text-right">
                        {formatCurrency(capital * a.percent / 100)}
                      </span>
                    </div>
                  </div>
                ))}
                <p className="text-[11px] text-zinc-500 mt-3 pt-3 border-t border-border">
                  Répartition basée sur le profil {profileLabels[portfolio.riskProfile].toLowerCase()} et les recommandations actuelles.
                </p>
              </div>
            );
          })()}
        </Card>
      </div>
    </div>
  );
}
