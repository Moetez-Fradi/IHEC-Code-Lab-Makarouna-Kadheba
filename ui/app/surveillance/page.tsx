"use client";

import { useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  ShieldAlert,
  AlertTriangle,
  Activity,
  Filter,
  Check,
  Clock,
  TrendingDown,
  Volume2,
  Search,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/ui/page-header";
import { ChartTooltip } from "@/components/ui/chart-tooltip";
import { Tabs } from "@/components/ui/tabs";
import { generateAlerts, type Alert, type AlertSeverity, type AlertType } from "@/lib/mock-data";
import { relativeTime, cn } from "@/lib/utils";

const SEVERITY_CONFIG: Record<AlertSeverity, { label: string; color: string; badge: "danger" | "warning" | "default" }> = {
  critical: { label: "Critique", color: "bg-danger", badge: "danger" },
  warning: { label: "Attention", color: "bg-warning", badge: "warning" },
  info: { label: "Info", color: "bg-accent-light", badge: "default" },
};

const TYPE_LABELS: Record<AlertType, { label: string; icon: typeof AlertTriangle }> = {
  volume_spike: { label: "Pic de volume", icon: Volume2 },
  price_anomaly: { label: "Variation anormale", icon: TrendingDown },
  suspicious_pattern: { label: "Pattern suspect", icon: ShieldAlert },
  liquidity_drop: { label: "Chute liquidité", icon: Activity },
};

export default function SurveillancePage() {
  const allAlerts = useMemo(() => generateAlerts(35), []);
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [acknowledged, setAcknowledged] = useState<Set<string>>(new Set());

  const filtered = useMemo(() => {
    return allAlerts.filter((a) => {
      if (severityFilter !== "all" && a.severity !== severityFilter) return false;
      if (typeFilter !== "all" && a.type !== typeFilter) return false;
      if (searchQuery && !a.ticker.toLowerCase().includes(searchQuery.toLowerCase()) && !a.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });
  }, [allAlerts, severityFilter, typeFilter, searchQuery]);

  const criticalCount = allAlerts.filter((a) => a.severity === "critical").length;
  const warningCount = allAlerts.filter((a) => a.severity === "warning").length;
  const unacknowledged = allAlerts.filter((a) => !a.acknowledged && !acknowledged.has(a.id)).length;

  // Distribution by type for chart
  const typeDistribution = useMemo(() => {
    const map = new Map<string, number>();
    allAlerts.forEach((a) => {
      map.set(a.type, (map.get(a.type) ?? 0) + 1);
    });
    return Array.from(map.entries()).map(([type, count]) => ({
      type: TYPE_LABELS[type as AlertType]?.label ?? type,
      count,
    }));
  }, [allAlerts]);

  // Distribution by day
  const dailyDistribution = useMemo(() => {
    const map = new Map<string, number>();
    allAlerts.forEach((a) => {
      const day = a.timestamp.slice(0, 10);
      map.set(day, (map.get(day) ?? 0) + 1);
    });
    return Array.from(map.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, count]) => ({ date: date.slice(5), count }));
  }, [allAlerts]);

  const toggleAcknowledge = (id: string) => {
    setAcknowledged((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="p-6 pb-20 md:pb-6 max-w-[1400px] mx-auto">
      <PageHeader
        title="Surveillance & Alertes"
        description="Détection d'anomalies et surveillance du marché en temps réel"
      />

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <StatCard
          label="Total alertes"
          value={String(allAlerts.length)}
          sub="7 derniers jours"
          icon={ShieldAlert}
        />
        <StatCard
          label="Critiques"
          value={String(criticalCount)}
          sub="Nécessitent une action"
          icon={AlertTriangle}
          trend="down"
        />
        <StatCard
          label="Avertissements"
          value={String(warningCount)}
          sub="À surveiller"
          icon={Activity}
          trend="neutral"
        />
        <StatCard
          label="Non traitées"
          value={String(unacknowledged)}
          sub="En attente"
          icon={Clock}
          trend={unacknowledged > 10 ? "down" : "neutral"}
        />
      </div>

      {/* Charts Row */}
      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Alertes par type</CardTitle>
          </CardHeader>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeDistribution} layout="vertical">
                <XAxis type="number" axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="type" axisLine={false} tickLine={false} width={120} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} name="Alertes" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Distribution journalière</CardTitle>
          </CardHeader>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dailyDistribution}>
                <XAxis dataKey="date" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} width={25} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Alertes" opacity={0.8} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-4" padding={false}>
        <div className="flex flex-wrap items-center gap-3 p-4">
          <Filter className="w-4 h-4 text-muted" />

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted" />
            <input
              type="text"
              placeholder="Rechercher par ticker ou titre..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-zinc-900 border border-border rounded-lg pl-8 pr-3 py-1.5 text-xs text-foreground w-56 focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>

          {/* Severity Filter */}
          <Tabs
            tabs={[
              { id: "all", label: "Toutes" },
              { id: "critical", label: "Critiques" },
              { id: "warning", label: "Attention" },
              { id: "info", label: "Info" },
            ]}
            defaultTab="all"
            onChange={setSeverityFilter}
          />

          {/* Type Filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-zinc-900 border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="all">Tous les types</option>
            <option value="volume_spike">Pic de volume</option>
            <option value="price_anomaly">Variation anormale</option>
            <option value="suspicious_pattern">Pattern suspect</option>
            <option value="liquidity_drop">Chute liquidité</option>
          </select>

          <span className="text-xs text-muted ml-auto">{filtered.length} résultat{filtered.length > 1 ? "s" : ""}</span>
        </div>
      </Card>

      {/* Alerts List */}
      <div className="space-y-2">
        {filtered.map((alert) => {
          const config = SEVERITY_CONFIG[alert.severity];
          const typeInfo = TYPE_LABELS[alert.type];
          const TypeIcon = typeInfo.icon;
          const isAck = alert.acknowledged || acknowledged.has(alert.id);

          return (
            <Card key={alert.id} padding={false} className={cn("transition-colors", isAck && "opacity-50")}>
              <div className="flex items-start gap-4 p-4">
                {/* Severity Dot */}
                <div className={cn("mt-1 w-2.5 h-2.5 rounded-full shrink-0", config.color)} />

                {/* Icon */}
                <div className="w-9 h-9 rounded-lg bg-zinc-800 flex items-center justify-center shrink-0">
                  <TypeIcon className="w-4 h-4 text-muted" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-medium text-foreground">{alert.title}</span>
                    <Badge variant={config.badge}>{config.label}</Badge>
                    <Badge variant="muted">{typeInfo.label}</Badge>
                  </div>
                  <p className="text-xs text-muted leading-relaxed">{alert.description}</p>
                  <div className="flex items-center gap-3 mt-2 text-[11px] text-zinc-500">
                    <span className="font-mono">{alert.id}</span>
                    <span>·</span>
                    <span className="font-medium text-foreground">{alert.ticker}</span>
                    <span>·</span>
                    <span>{relativeTime(alert.timestamp)}</span>
                    <span>·</span>
                    <span>{new Date(alert.timestamp).toLocaleString("fr-TN")}</span>
                  </div>
                </div>

                {/* Action */}
                <button
                  onClick={() => toggleAcknowledge(alert.id)}
                  className={cn(
                    "shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border",
                    isAck
                      ? "border-success/30 text-success bg-success/5"
                      : "border-border text-muted hover:text-foreground hover:bg-card-hover"
                  )}
                >
                  <Check className="w-3.5 h-3.5" />
                  {isAck ? "Traitée" : "Acquitter"}
                </button>
              </div>
            </Card>
          );
        })}

        {filtered.length === 0 && (
          <div className="text-center py-12 text-muted text-sm">
            Aucune alerte ne correspond aux filtres sélectionnés.
          </div>
        )}
      </div>
    </div>
  );
}
