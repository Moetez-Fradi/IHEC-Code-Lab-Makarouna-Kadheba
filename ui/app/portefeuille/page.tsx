"use client";

import { useEffect, useMemo, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Wallet,
  TrendingUp,
  ShieldAlert,
  Globe,
  Loader2,
  AlertTriangle,
  Play,
  Zap,
  BarChart3,
  Info,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import { StatCard } from "@/components/ui/stat-card";
import { Tabs } from "@/components/ui/tabs";
import { ChartTooltip } from "@/components/ui/chart-tooltip";
import { useAuth } from "@/lib/auth-context";
import { formatCurrency, formatPercent, formatNumber } from "@/lib/utils";
import {
  apiPortfolioRecommend,
  apiPortfolioSimulate,
  apiPortfolioStressTest,
  apiPortfolioMacro,
  type PortfolioRecommendation,
  type PortfolioSimulation,
  type PortfolioStressTest,
  type MacroData,
} from "@/lib/api";

const PROFILES = [
  { id: "conservateur", label: "Conservateur" },
  { id: "modere", label: "Modéré" },
  { id: "agressif", label: "Agressif" },
];

const STRESS_TYPES = [
  { id: "sector_crash", label: "Crash sectoriel" },
  { id: "liquidity_shock", label: "Choc de liquidité" },
  { id: "interest_rate_spike", label: "Hausse des taux" },
  { id: "currency_depreciation", label: "Dépréciation TND" },
  { id: "company_specific", label: "Risque spécifique" },
];

const PIE_COLORS = [
  "#3b82f6", "#f59e0b", "#10b981", "#ef4444",
  "#8b5cf6", "#06b6d4", "#ec4899", "#f97316",
];

export default function PortfolioPage() {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState("recommend");

  // ── Recommend state ──
  const [profile, setProfile] = useState("modere");
  const [recommendation, setRecommendation] = useState<PortfolioRecommendation | null>(null);
  const [recLoading, setRecLoading] = useState(false);
  const [recError, setRecError] = useState<string | null>(null);

  // ── Simulate state ──
  const [simProfile, setSimProfile] = useState("modere");
  const [simCapital, setSimCapital] = useState("100000");
  const [simDays, setSimDays] = useState("");
  const [simulation, setSimulation] = useState<PortfolioSimulation | null>(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState<string | null>(null);

  // ── Stress state ──
  const [stressType, setStressType] = useState("sector_crash");
  const [stressIntensity, setStressIntensity] = useState("0.20");
  const [stressResult, setStressResult] = useState<PortfolioStressTest | null>(null);
  const [stressLoading, setStressLoading] = useState(false);
  const [stressError, setStressError] = useState<string | null>(null);

  // ── Macro state ──
  const [macro, setMacro] = useState<MacroData | null>(null);
  const [macroLoading, setMacroLoading] = useState(false);
  const [macroError, setMacroError] = useState<string | null>(null);

  // ── Handlers ──
  const handleRecommend = () => {
    if (!token) return;
    setRecLoading(true);
    setRecError(null);
    setRecommendation(null);
    apiPortfolioRecommend(token, profile)
      .then(setRecommendation)
      .catch((e) => setRecError(e.message))
      .finally(() => setRecLoading(false));
  };

  const handleSimulate = () => {
    if (!token) return;
    setSimLoading(true);
    setSimError(null);
    setSimulation(null);
    const capital = simCapital ? parseFloat(simCapital) : undefined;
    const days = simDays ? parseInt(simDays, 10) : undefined;
    apiPortfolioSimulate(token, simProfile, capital, days)
      .then(setSimulation)
      .catch((e) => setSimError(e.message))
      .finally(() => setSimLoading(false));
  };

  const handleStressTest = () => {
    if (!token) return;
    setStressLoading(true);
    setStressError(null);
    setStressResult(null);
    apiPortfolioStressTest(token, stressType, parseFloat(stressIntensity))
      .then(setStressResult)
      .catch((e) => setStressError(e.message))
      .finally(() => setStressLoading(false));
  };

  useEffect(() => {
    if (activeTab === "macro" && !macro && !macroLoading && token) {
      setMacroLoading(true);
      setMacroError(null);
      apiPortfolioMacro(token)
        .then(setMacro)
        .catch((e) => setMacroError(e.message))
        .finally(() => setMacroLoading(false));
    }
  }, [activeTab, token]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Pie chart data ──
  const weightData = useMemo(() => {
    if (!recommendation) return [];
    return Object.entries(recommendation.weights)
      .map(([name, value]) => ({ name, value: parseFloat((value * 100).toFixed(2)) }))
      .sort((a, b) => b.value - a.value);
  }, [recommendation]);

  // ── Simulation chart data ──
  const simChartData = useMemo(() => {
    if (!simulation) return [];
    return simulation.daily_values.map((v, i) => ({
      day: i + 1,
      value: v,
    }));
  }, [simulation]);

  return (
    <div className="p-6 pb-20 md:pb-6 max-w-[1400px] mx-auto">
      <PageHeader
        title="Mon portefeuille"
        description="Optimisation RL, simulation et analyse de risque"
      />

      <Tabs
        tabs={[
          { id: "recommend", label: "Recommandation" },
          { id: "simulate", label: "Simulation" },
          { id: "stress", label: "Stress Test" },
          { id: "macro", label: "Macro" },
        ]}
        defaultTab="recommend"
        onChange={setActiveTab}
        className="mb-6"
      />

      {/* ──────────── RECOMMEND TAB ──────────── */}
      {activeTab === "recommend" && (
        <div>
          {/* Controls */}
          <Card className="mb-6">
            <div className="flex flex-col sm:flex-row sm:items-end gap-4">
              <div className="flex-1">
                <label className="text-xs text-muted font-medium uppercase tracking-wide mb-2 block">
                  Profil de risque
                </label>
                <select
                  value={profile}
                  onChange={(e) => setProfile(e.target.value)}
                  className="w-full bg-zinc-900 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                >
                  {PROFILES.map((p) => (
                    <option key={p.id} value={p.id}>{p.label}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleRecommend}
                disabled={recLoading}
                className="flex items-center gap-2 px-5 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent/90 transition-colors disabled:opacity-50"
              >
                {recLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {recLoading ? "Optimisation en cours..." : "Obtenir une recommandation"}
              </button>
            </div>
          </Card>

          {recError && (
            <Card className="mb-6 border-danger/30">
              <div className="flex items-center gap-3 text-danger">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <div>
                  <p className="text-sm font-medium">Erreur</p>
                  <p className="text-xs text-zinc-400 mt-1">{recError}</p>
                </div>
              </div>
            </Card>
          )}

          {recLoading && (
            <div className="flex items-center justify-center h-[40vh]">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-8 h-8 text-accent animate-spin" />
                <span className="text-sm text-muted">Entraînement du modèle RL et calcul des poids...</span>
                <span className="text-xs text-zinc-600">Cela peut prendre quelques secondes</span>
              </div>
            </div>
          )}

          {recommendation && !recLoading && (
            <>
              {/* Profile badge */}
              <Card className="mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent/20 to-accent/5 flex items-center justify-center">
                    <Wallet className="w-6 h-6 text-accent" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-foreground">Allocation optimale</h2>
                    <p className="text-xs text-muted">
                      Profil : <Badge variant="info" className="ml-1">{recommendation.profile}</Badge>
                    </p>
                  </div>
                </div>
              </Card>

              {/* KPIs */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <StatCard
                  label="Ratio Sharpe"
                  value={recommendation.metrics.sharpe?.toFixed(3) ?? "N/A"}
                  icon={TrendingUp}
                  trend={
                    (recommendation.metrics.sharpe ?? 0) > 1
                      ? "up"
                      : (recommendation.metrics.sharpe ?? 0) < 0
                      ? "down"
                      : "neutral"
                  }
                />
                <StatCard
                  label="Ratio Sortino"
                  value={recommendation.metrics.sortino?.toFixed(3) ?? "N/A"}
                  icon={TrendingUp}
                  trend={
                    (recommendation.metrics.sortino ?? 0) > 1
                      ? "up"
                      : (recommendation.metrics.sortino ?? 0) < 0
                      ? "down"
                      : "neutral"
                  }
                />
                <StatCard
                  label="Max Drawdown"
                  value={
                    recommendation.metrics.max_drawdown != null
                      ? `${(recommendation.metrics.max_drawdown * 100).toFixed(2)}%`
                      : "N/A"
                  }
                  icon={ShieldAlert}
                  trend={
                    (recommendation.metrics.max_drawdown ?? 0) > -0.1
                      ? "up"
                      : "down"
                  }
                />
                <StatCard
                  label="Volatilité"
                  value={
                    recommendation.metrics.volatility != null
                      ? `${(recommendation.metrics.volatility * 100).toFixed(2)}%`
                      : "N/A"
                  }
                  icon={BarChart3}
                />
              </div>

              {/* Weights Chart + Table */}
              <div className="grid md:grid-cols-2 gap-4 mb-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Wallet className="w-4 h-4 text-accent" />
                      Répartition du portefeuille
                    </CardTitle>
                  </CardHeader>
                  <div className="h-[300px] flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={weightData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="value"
                          nameKey="name"
                          label={({ name, value }) => `${name} ${value}%`}
                        >
                          {weightData.map((_, idx) => (
                            <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          content={<ChartTooltip formatter={(v) => `${v}%`} />}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Poids par actif</CardTitle>
                  </CardHeader>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border text-[11px] text-muted uppercase tracking-wide">
                          <th className="text-left py-2 pr-4">Actif</th>
                          <th className="text-right py-2 pl-3">Poids</th>
                        </tr>
                      </thead>
                      <tbody>
                        {weightData.map((w, i) => (
                          <tr key={w.name} className="border-b border-border/50 hover:bg-card-hover transition-colors">
                            <td className="py-2.5 pr-4">
                              <div className="flex items-center gap-2">
                                <span
                                  className="w-3 h-3 rounded-full shrink-0"
                                  style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
                                />
                                <span className="font-medium text-foreground">{w.name}</span>
                              </div>
                            </td>
                            <td className="py-2.5 pl-3 text-right font-semibold text-foreground">
                              {w.value.toFixed(2)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              </div>

              {/* Explanation */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Info className="w-4 h-4 text-muted" />
                    Explication IA
                  </CardTitle>
                </CardHeader>
                <div className="prose prose-invert prose-sm max-w-none">
                  <p className="text-sm text-zinc-300 whitespace-pre-wrap leading-relaxed">
                    {recommendation.explanation}
                  </p>
                </div>
              </Card>
            </>
          )}
        </div>
      )}

      {/* ──────────── SIMULATE TAB ──────────── */}
      {activeTab === "simulate" && (
        <div>
          <Card className="mb-6">
            <div className="grid sm:grid-cols-4 gap-4">
              <div>
                <label className="text-xs text-muted font-medium uppercase tracking-wide mb-2 block">
                  Profil
                </label>
                <select
                  value={simProfile}
                  onChange={(e) => setSimProfile(e.target.value)}
                  className="w-full bg-zinc-900 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                >
                  {PROFILES.map((p) => (
                    <option key={p.id} value={p.id}>{p.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-muted font-medium uppercase tracking-wide mb-2 block">
                  Capital (TND)
                </label>
                <input
                  type="number"
                  value={simCapital}
                  onChange={(e) => setSimCapital(e.target.value)}
                  placeholder="100000"
                  className="w-full bg-zinc-900 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
              <div>
                <label className="text-xs text-muted font-medium uppercase tracking-wide mb-2 block">
                  Jours (optionnel)
                </label>
                <input
                  type="number"
                  value={simDays}
                  onChange={(e) => setSimDays(e.target.value)}
                  placeholder="Auto"
                  className="w-full bg-zinc-900 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleSimulate}
                  disabled={simLoading}
                  className="w-full flex items-center justify-center gap-2 px-5 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent/90 transition-colors disabled:opacity-50"
                >
                  {simLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  Simuler
                </button>
              </div>
            </div>
          </Card>

          {simError && (
            <Card className="mb-6 border-danger/30">
              <div className="flex items-center gap-3 text-danger">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <div>
                  <p className="text-sm font-medium">Erreur</p>
                  <p className="text-xs text-zinc-400 mt-1">{simError}</p>
                </div>
              </div>
            </Card>
          )}

          {simLoading && (
            <div className="flex items-center justify-center h-[40vh]">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-8 h-8 text-accent animate-spin" />
                <span className="text-sm text-muted">Simulation en cours...</span>
              </div>
            </div>
          )}

          {simulation && !simLoading && (
            <>
              {/* KPIs */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <StatCard
                  label="Capital initial"
                  value={formatCurrency(simulation.initial_capital)}
                  icon={Wallet}
                />
                <StatCard
                  label="Valeur finale"
                  value={formatCurrency(simulation.final_value)}
                  icon={TrendingUp}
                  trend={simulation.final_value >= simulation.initial_capital ? "up" : "down"}
                />
                <StatCard
                  label="ROI"
                  value={formatPercent(simulation.roi * 100)}
                  icon={TrendingUp}
                  trend={simulation.roi >= 0 ? "up" : "down"}
                />
                <StatCard
                  label="Sharpe"
                  value={simulation.sharpe.toFixed(3)}
                  icon={BarChart3}
                  trend={simulation.sharpe > 1 ? "up" : simulation.sharpe < 0 ? "down" : "neutral"}
                />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <StatCard
                  label="Sortino"
                  value={simulation.sortino.toFixed(3)}
                  icon={BarChart3}
                />
                <StatCard
                  label="Max Drawdown"
                  value={`${(simulation.max_drawdown * 100).toFixed(2)}%`}
                  icon={ShieldAlert}
                  trend={simulation.max_drawdown > -0.1 ? "up" : "down"}
                />
                <StatCard
                  label="Volatilité"
                  value={`${(simulation.volatility * 100).toFixed(2)}%`}
                  icon={BarChart3}
                />
                <StatCard
                  label="Durée"
                  value={`${simulation.n_days} jours`}
                  icon={BarChart3}
                />
              </div>

              {/* Equity curve */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-accent" />
                    Courbe de valeur du portefeuille
                  </CardTitle>
                </CardHeader>
                <div className="h-[350px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={simChartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                      <XAxis
                        dataKey="day"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 11 }}
                        label={{ value: "Jour", position: "insideBottom", offset: -5, fontSize: 11 }}
                      />
                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        width={70}
                        tick={{ fontSize: 11 }}
                        tickFormatter={(v: number) => formatNumber(v)}
                      />
                      <Tooltip content={<ChartTooltip formatter={(v) => formatCurrency(v)} />} />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={false}
                        name="Valeur (TND)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </>
          )}
        </div>
      )}

      {/* ──────────── STRESS TEST TAB ──────────── */}
      {activeTab === "stress" && (
        <div>
          <Card className="mb-6">
            <div className="grid sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs text-muted font-medium uppercase tracking-wide mb-2 block">
                  Type de stress
                </label>
                <select
                  value={stressType}
                  onChange={(e) => setStressType(e.target.value)}
                  className="w-full bg-zinc-900 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                >
                  {STRESS_TYPES.map((s) => (
                    <option key={s.id} value={s.id}>{s.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-muted font-medium uppercase tracking-wide mb-2 block">
                  Intensité (0–1)
                </label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={stressIntensity}
                  onChange={(e) => setStressIntensity(e.target.value)}
                  className="w-full bg-zinc-900 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleStressTest}
                  disabled={stressLoading}
                  className="w-full flex items-center justify-center gap-2 px-5 py-2 rounded-lg bg-danger text-white text-sm font-medium hover:bg-danger/90 transition-colors disabled:opacity-50"
                >
                  {stressLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Zap className="w-4 h-4" />
                  )}
                  Lancer le stress test
                </button>
              </div>
            </div>
          </Card>

          {stressError && (
            <Card className="mb-6 border-danger/30">
              <div className="flex items-center gap-3 text-danger">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <div>
                  <p className="text-sm font-medium">Erreur</p>
                  <p className="text-xs text-zinc-400 mt-1">{stressError}</p>
                </div>
              </div>
            </Card>
          )}

          {stressLoading && (
            <div className="flex items-center justify-center h-[40vh]">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-8 h-8 text-accent animate-spin" />
                <span className="text-sm text-muted">Stress test en cours...</span>
              </div>
            </div>
          )}

          {stressResult && !stressLoading && (
            <div className="grid md:grid-cols-3 gap-4 mb-6">
              <StatCard
                label="Valeur pré-stress"
                value={formatCurrency(stressResult.pre_stress.value)}
                icon={Wallet}
              />
              <StatCard
                label="Valeur post-stress"
                value={formatCurrency(stressResult.post_stress.value)}
                icon={ShieldAlert}
                trend={stressResult.impact >= 0 ? "up" : "down"}
              />
              <StatCard
                label="Impact"
                value={formatCurrency(stressResult.impact)}
                sub={`${((stressResult.impact / stressResult.pre_stress.value) * 100).toFixed(2)}% du portefeuille`}
                icon={Zap}
                trend={stressResult.impact >= 0 ? "up" : "down"}
              />
            </div>
          )}

          {stressResult && !stressLoading && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-danger" />
                  Résultat du stress test
                </CardTitle>
              </CardHeader>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { label: "Avant", value: stressResult.pre_stress.value },
                      { label: "Après", value: stressResult.post_stress.value },
                    ]}
                    margin={{ top: 5, right: 20, bottom: 5, left: 10 }}
                  >
                    <XAxis dataKey="label" axisLine={false} tickLine={false} />
                    <YAxis axisLine={false} tickLine={false} width={70} tickFormatter={(v: number) => formatNumber(v)} />
                    <Tooltip content={<ChartTooltip formatter={(v) => formatCurrency(v)} />} />
                    <Bar dataKey="value" name="Valeur (TND)" radius={[6, 6, 0, 0]}>
                      <Cell fill="#3b82f6" />
                      <Cell fill="#ef4444" />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="text-[11px] text-zinc-500 mt-4 pt-3 border-t border-border">
                Type : {STRESS_TYPES.find((s) => s.id === stressType)?.label ?? stressType} · Intensité : {(parseFloat(stressIntensity) * 100).toFixed(0)}%
              </p>
            </Card>
          )}
        </div>
      )}

      {/* ──────────── MACRO TAB ──────────── */}
      {activeTab === "macro" && (
        <div>
          {macroError && (
            <Card className="mb-6 border-danger/30">
              <div className="flex items-center gap-3 text-danger">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <div>
                  <p className="text-sm font-medium">Erreur</p>
                  <p className="text-xs text-zinc-400 mt-1">{macroError}</p>
                </div>
              </div>
            </Card>
          )}

          {macroLoading && (
            <div className="flex items-center justify-center h-[40vh]">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-8 h-8 text-accent animate-spin" />
                <span className="text-sm text-muted">Chargement des données macro...</span>
              </div>
            </div>
          )}

          {macro && !macroLoading && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-accent" />
                  Indicateurs macroéconomiques (Tunisie)
                </CardTitle>
              </CardHeader>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-[11px] text-muted uppercase tracking-wide">
                      <th className="text-left py-2 pr-4">Indicateur</th>
                      <th className="text-right py-2 pl-3">Valeur</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(macro.data).map(([key, val]) => (
                      <tr key={key} className="border-b border-border/50 hover:bg-card-hover transition-colors">
                        <td className="py-2.5 pr-4 font-medium text-foreground">{key}</td>
                        <td className="py-2.5 pl-3 text-right text-foreground">
                          {typeof val === "number" ? val.toFixed(2) : String(val)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-[11px] text-zinc-500 mt-4 pt-3 border-t border-border">
                Sources : Banque Mondiale, FMI, Banque Centrale de Tunisie · Données les plus récentes disponibles
              </p>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
