"use client";

import { useEffect, useMemo, useState, Suspense } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Cell,
  CartesianGrid,
} from "recharts";
import {
  ShieldAlert,
  AlertTriangle,
  Activity,
  TrendingDown,
  Loader2,
  Calendar,
  Zap,
  Eye,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import { StatCard } from "@/components/ui/stat-card";
import { ChartTooltip } from "@/components/ui/chart-tooltip";
import { Tabs } from "@/components/ui/tabs";
import { useAuth } from "@/lib/auth-context";
import {
  apiGetStocks,
  apiGetAnomalies,
  type AnomalyReport,
  type Anomaly,
} from "@/lib/api";
import { formatNumber } from "@/lib/utils";

/* ── Helpers ────────────────────────────────────────────────────────────── */

function severityVariant(s: number): "danger" | "warning" | "muted" {
  if (s >= 0.3) return "danger";
  if (s >= 0.1) return "warning";
  return "muted";
}

function severityLabel(s: number) {
  if (s >= 0.3) return "Élevée";
  if (s >= 0.1) return "Moyenne";
  return "Faible";
}

function typeColor(t: string) {
  if (t === "volume") return "#3b82f6";
  if (t === "price") return "#ef4444";
  return "#f59e0b"; // pattern
}

function typeLabel(t: string) {
  if (t === "volume") return "Volume";
  if (t === "price") return "Prix";
  return "Pattern";
}

function defaultDateRange() {
  const end = new Date();
  const start = new Date();
  start.setFullYear(start.getFullYear() - 1);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

/* ── Main content ───────────────────────────────────────────────────────── */

function SurveillanceContent() {
  const { token } = useAuth();

  const [stockList, setStockList] = useState<{ code: string; valeur: string }[]>([]);
  const [selectedCode, setSelectedCode] = useState("");
  const [dateRange, setDateRange] = useState(defaultDateRange);
  const [report, setReport] = useState<AnomalyReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  // Load stock list
  useEffect(() => {
    if (!token) return;
    apiGetStocks(token)
      .then((list) => {
        setStockList(list);
        if (!selectedCode && list.length > 0) setSelectedCode(list[0].code);
      })
      .catch(console.error);
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load anomalies when stock or date range changes
  useEffect(() => {
    if (!token || !selectedCode) return;
    setLoading(true);
    setError(null);
    setReport(null);
    apiGetAnomalies(token, selectedCode, dateRange.start, dateRange.end)
      .then(setReport)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [token, selectedCode, dateRange]);

  // ── Derived data ──

  const stockName = useMemo(
    () => stockList.find((s) => s.code === selectedCode)?.valeur ?? selectedCode,
    [stockList, selectedCode],
  );

  const filteredAnomalies = useMemo(() => {
    if (!report) return [];
    if (typeFilter === "all") return report.anomalies;
    return report.anomalies.filter((a) => a.types.includes(typeFilter));
  }, [report, typeFilter]);

  // Timeline chart data — severity by date
  const timelineData = useMemo(() => {
    if (!report) return [];
    return report.anomalies.map((a) => ({
      date: a.date,
      severity: a.severity,
      types: a.types.join(", "),
      primaryType: a.types[0],
    }));
  }, [report]);

  // Type distribution for bar chart
  const typeDistribution = useMemo(() => {
    if (!report) return [];
    const counts = report.summary.type_counts;
    return Object.entries(counts).map(([type, count]) => ({
      type: typeLabel(type),
      count,
      fill: typeColor(type),
    }));
  }, [report]);

  // Monthly grouping
  const monthlyData = useMemo(() => {
    if (!report) return [];
    const groups: Record<string, number> = {};
    report.anomalies.forEach((a) => {
      const month = a.date.slice(0, 7); // YYYY-MM
      groups[month] = (groups[month] || 0) + 1;
    });
    return Object.entries(groups)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([month, count]) => ({ month, count }));
  }, [report]);

  // ── Loading State ──
  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-accent animate-spin" />
          <span className="text-sm text-muted">Analyse des anomalies en cours...</span>
          <span className="text-xs text-zinc-600">Détection sur la période sélectionnée</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 pb-20 md:pb-6 max-w-[1400px] mx-auto">
      <PageHeader
        title="Surveillance & Alertes"
        description="Détection d'anomalies et surveillance du marché"
      >
        <div className="flex items-center gap-2 flex-wrap">
          {/* Stock picker */}
          <select
            value={selectedCode}
            onChange={(e) => setSelectedCode(e.target.value)}
            className="bg-zinc-900 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
          >
            {stockList.map((s) => (
              <option key={s.code} value={s.code}>
                {s.code} — {s.valeur}
              </option>
            ))}
          </select>

          {/* Date range */}
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => setDateRange((r) => ({ ...r, start: e.target.value }))}
            className="bg-zinc-900 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
          />
          <span className="text-muted text-xs">&rarr;</span>
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => setDateRange((r) => ({ ...r, end: e.target.value }))}
            className="bg-zinc-900 border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
      </PageHeader>

      {/* Error */}
      {error && (
        <Card className="mb-6 border-danger/30">
          <div className="flex items-center gap-3 text-danger">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <div>
              <p className="text-sm font-medium">Erreur de détection</p>
              <p className="text-xs text-zinc-400 mt-1">{error}</p>
            </div>
          </div>
        </Card>
      )}

      {report && (
        <>
          {/* ── KPI Cards ── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard
              label="Jours analysés"
              value={report.total_days.toString()}
              sub={`${report.start} \u2192 ${report.end}`}
              icon={Calendar}
            />
            <StatCard
              label="Anomalies détectées"
              value={report.anomaly_days.toString()}
              sub={`${((report.anomaly_days / report.total_days) * 100).toFixed(1)}% des jours`}
              icon={ShieldAlert}
              trend={report.anomaly_days > 20 ? "down" : report.anomaly_days > 10 ? "neutral" : "up"}
            />
            <StatCard
              label="Sévérité moyenne"
              value={report.summary.avg_severity.toFixed(3)}
              sub={severityLabel(report.summary.avg_severity)}
              icon={Zap}
              trend={report.summary.avg_severity >= 0.3 ? "down" : report.summary.avg_severity >= 0.1 ? "neutral" : "up"}
            />
            <StatCard
              label="Sévérité max"
              value={report.summary.max_severity.toFixed(3)}
              sub={severityLabel(report.summary.max_severity)}
              icon={AlertTriangle}
              trend={report.summary.max_severity >= 0.3 ? "down" : "neutral"}
            />
          </div>

          {/* ── Stock Header + Type Badges ── */}
          <Card className="mb-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent/20 to-accent/5 flex items-center justify-center">
                  <Eye className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-foreground">{stockName}</h2>
                  <p className="text-xs text-muted">{selectedCode} &middot; Surveillance d&apos;anomalies</p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="info">
                  <Activity className="w-3 h-3 mr-1 inline" />
                  Volume: {report.summary.volume_anomalies}
                </Badge>
                <Badge variant="danger">
                  <TrendingDown className="w-3 h-3 mr-1 inline" />
                  Prix: {report.summary.price_anomalies}
                </Badge>
                <Badge variant="warning">
                  <Zap className="w-3 h-3 mr-1 inline" />
                  Pattern: {report.summary.pattern_anomalies}
                </Badge>
              </div>
            </div>
          </Card>

          {/* ── Charts Row ── */}
          <div className="grid md:grid-cols-2 gap-4 mb-6">
            {/* Severity Timeline (Scatter) */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-accent" />
                  Chronologie des anomalies
                </CardTitle>
              </CardHeader>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(d: string) => d.slice(5)}
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 10 }}
                    />
                    <YAxis
                      dataKey="severity"
                      domain={[0, "auto"]}
                      axisLine={false}
                      tickLine={false}
                      width={45}
                      tick={{ fontSize: 11 }}
                      label={{ value: "Sévérité", angle: -90, position: "insideLeft", style: { fontSize: 10, fill: "#71717a" } }}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (!active || !payload?.length) return null;
                        const d = payload[0].payload;
                        return (
                          <div className="rounded-lg border border-border bg-zinc-900 px-3 py-2 shadow-xl text-xs">
                            <p className="text-muted mb-1">{d.date}</p>
                            <p className="text-foreground font-medium">Sévérité: {d.severity.toFixed(4)}</p>
                            <p className="text-muted">Types: {d.types}</p>
                          </div>
                        );
                      }}
                    />
                    <Scatter data={timelineData} name="Anomalies">
                      {timelineData.map((entry, i) => (
                        <Cell
                          key={i}
                          fill={typeColor(entry.primaryType)}
                          opacity={0.8}
                        />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Anomalies par mois */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-muted" />
                  Anomalies par mois
                </CardTitle>
              </CardHeader>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={monthlyData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                    <XAxis
                      dataKey="month"
                      tickFormatter={(m: string) => {
                        const [y, mo] = m.split("-");
                        return `${mo}/${y.slice(2)}`;
                      }}
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis axisLine={false} tickLine={false} width={30} tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="count" fill="#2563eb" opacity={0.7} name="Anomalies" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          {/* ── Type Distribution Cards ── */}
          <div className="grid md:grid-cols-3 gap-4 mb-6">
            {typeDistribution.map((td) => (
              <Card key={td.type} className="flex items-center gap-4">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                  style={{ backgroundColor: `${td.fill}20` }}
                >
                  <span className="text-lg font-bold" style={{ color: td.fill }}>
                    {td.count}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">Anomalies {td.type}</p>
                  <p className="text-xs text-muted">
                    {report.anomaly_days > 0
                      ? `${((td.count / report.anomaly_days) * 100).toFixed(0)}% du total`
                      : "0%"}
                  </p>
                </div>
              </Card>
            ))}
          </div>

          {/* ── Anomalies Table ── */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Détail des anomalies</CardTitle>
              <Tabs
                tabs={[
                  { id: "all", label: "Toutes" },
                  { id: "volume", label: "Volume" },
                  { id: "price", label: "Prix" },
                  { id: "pattern", label: "Pattern" },
                ]}
                defaultTab="all"
                onChange={setTypeFilter}
              />
            </CardHeader>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-[11px] text-muted uppercase tracking-wide">
                    <th className="text-left py-2 pr-4">Date</th>
                    <th className="text-left py-2 px-3">Types</th>
                    <th className="text-right py-2 px-3">Sévérité</th>
                    <th className="text-right py-2 px-3">Clôture</th>
                    <th className="text-right py-2 px-3">Volume</th>
                    <th className="text-right py-2 px-3">Var. Prix</th>
                    <th className="text-right py-2 px-3">Z-Score Vol.</th>
                    <th className="text-center py-2 pl-3">Détails</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAnomalies.length === 0 && (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-muted text-sm">
                        Aucune anomalie trouvée pour ce filtre.
                      </td>
                    </tr>
                  )}
                  {filteredAnomalies.map((a) => (
                    <AnomalyRow
                      key={a.date}
                      anomaly={a}
                      expanded={expandedRow === a.date}
                      onToggle={() => setExpandedRow(expandedRow === a.date ? null : a.date)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* ── Footer note ── */}
          <p className="text-[11px] text-zinc-500 mt-2">
            La détection combine trois méthodes : seuil de z-score sur le volume, variation de prix anormale, et Isolation Forest pour les patterns multi-dimensionnels.
            Les sévérités sont pondérées et normalisées. Période analysée : {report.start} &rarr; {report.end}.
          </p>
        </>
      )}
    </div>
  );
}

/* ── Anomaly Table Row ──────────────────────────────────────────────────── */

function AnomalyRow({
  anomaly,
  expanded,
  onToggle,
}: {
  anomaly: Anomaly;
  expanded: boolean;
  onToggle: () => void;
}) {
  const d = anomaly.details;

  return (
    <>
      <tr
        className="border-b border-border/50 hover:bg-card-hover transition-colors cursor-pointer"
        onClick={onToggle}
      >
        <td className="py-2.5 pr-4 font-medium text-foreground">{anomaly.date}</td>
        <td className="py-2.5 px-3">
          <div className="flex gap-1 flex-wrap">
            {anomaly.types.map((t) => (
              <Badge
                key={t}
                variant={t === "price" ? "danger" : t === "volume" ? "info" : "warning"}
              >
                {typeLabel(t)}
              </Badge>
            ))}
          </div>
        </td>
        <td className="py-2.5 px-3 text-right">
          <Badge variant={severityVariant(anomaly.severity)}>
            {anomaly.severity.toFixed(4)}
          </Badge>
        </td>
        <td className="py-2.5 px-3 text-right text-foreground">
          {d.CLOTURE > 0 ? `${d.CLOTURE.toFixed(2)} TND` : "\u2014"}
        </td>
        <td className="py-2.5 px-3 text-right text-foreground">
          {formatNumber(d.QUANTITE_NEGOCIEE)}
        </td>
        <td className="py-2.5 px-3 text-right">
          <span
            className={
              d.price_change_pct > 0
                ? "text-success"
                : d.price_change_pct < 0
                  ? "text-danger"
                  : "text-muted"
            }
          >
            {d.price_change_pct >= 0 ? "+" : ""}
            {d.price_change_pct.toFixed(2)}%
          </span>
        </td>
        <td className="py-2.5 px-3 text-right font-mono text-xs text-foreground">
          {d.volume_zscore.toFixed(2)}
        </td>
        <td className="py-2.5 pl-3 text-center">
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-muted inline" />
          ) : (
            <ChevronDown className="w-4 h-4 text-muted inline" />
          )}
        </td>
      </tr>

      {/* Expanded detail row */}
      {expanded && (
        <tr className="bg-zinc-900/50">
          <td colSpan={8} className="px-4 py-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="text-muted block mb-0.5">Ouverture</span>
                <span className="text-foreground font-medium">{d.OUVERTURE.toFixed(2)} TND</span>
              </div>
              <div>
                <span className="text-muted block mb-0.5">Clôture</span>
                <span className="text-foreground font-medium">
                  {d.CLOTURE > 0 ? `${d.CLOTURE.toFixed(2)} TND` : "\u2014"}
                </span>
              </div>
              <div>
                <span className="text-muted block mb-0.5">Nb Transactions</span>
                <span className="text-foreground font-medium">{formatNumber(d.NB_TRANSACTION)}</span>
              </div>
              <div>
                <span className="text-muted block mb-0.5">Capitaux</span>
                <span className="text-foreground font-medium">{formatNumber(d.CAPITAUX)} TND</span>
              </div>
              <div>
                <span className="text-muted block mb-0.5">Volume négocié</span>
                <span className="text-foreground font-medium">{formatNumber(d.QUANTITE_NEGOCIEE)}</span>
              </div>
              <div>
                <span className="text-muted block mb-0.5">Z-Score Volume</span>
                <span
                  className={`font-medium ${Math.abs(d.volume_zscore) > 3 ? "text-danger" : "text-foreground"}`}
                >
                  {d.volume_zscore.toFixed(4)}
                </span>
              </div>
              <div>
                <span className="text-muted block mb-0.5">Variation Prix</span>
                <span
                  className={`font-medium ${
                    d.price_change_pct > 0 ? "text-success" : d.price_change_pct < 0 ? "text-danger" : "text-muted"
                  }`}
                >
                  {d.price_change_pct >= 0 ? "+" : ""}
                  {d.price_change_pct.toFixed(2)}%
                </span>
              </div>
              <div>
                <span className="text-muted block mb-0.5">Score Isolation</span>
                <span
                  className={`font-medium ${d.isolation_score < -0.1 ? "text-warning" : "text-foreground"}`}
                >
                  {d.isolation_score.toFixed(4)}
                </span>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

/* ── Page export ─────────────────────────────────────────────────────────── */

export default function SurveillancePage() {
  return (
    <Suspense fallback={<div className="p-6 text-muted">Chargement...</div>}>
      <SurveillanceContent />
    </Suspense>
  );
}
