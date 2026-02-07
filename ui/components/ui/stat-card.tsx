import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  icon?: LucideIcon;
  trend?: "up" | "down" | "neutral";
  className?: string;
}

export function StatCard({ label, value, sub, icon: Icon, trend, className }: StatCardProps) {
  return (
    <div className={cn("rounded-xl border border-border bg-card p-4", className)}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-muted font-medium uppercase tracking-wide">{label}</span>
        {Icon && (
          <div className="w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center">
            <Icon className="w-4 h-4 text-muted" />
          </div>
        )}
      </div>
      <p className="text-xl font-semibold text-foreground tracking-tight">{value}</p>
      {sub && (
        <p
          className={cn(
            "text-xs mt-1 font-medium",
            trend === "up" && "text-success",
            trend === "down" && "text-danger",
            trend === "neutral" && "text-muted",
            !trend && "text-muted"
          )}
        >
          {sub}
        </p>
      )}
    </div>
  );
}
