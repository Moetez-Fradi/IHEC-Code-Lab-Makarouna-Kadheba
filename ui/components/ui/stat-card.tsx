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
    <div className={cn(
      "group relative overflow-hidden rounded-xl border border-border bg-gradient-to-br from-card to-card/50 p-5 transition-all hover:shadow-lg hover:border-accent/50",
      className
    )}>
      {/* Background gradient effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-accent/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      
      <div className="relative">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
            {label}
          </span>
          {Icon && (
            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center group-hover:bg-accent/20 transition-colors">
              <Icon className="w-5 h-5 text-accent" />
            </div>
          )}
        </div>
        <p className="text-2xl font-bold text-foreground tracking-tight mb-1">
          {value}
        </p>
        {sub && (
          <p
            className={cn(
              "text-xs font-medium",
              trend === "up" && "text-green-500",
              trend === "down" && "text-red-500",
              trend === "neutral" && "text-muted-foreground",
              !trend && "text-muted-foreground"
            )}
          >
            {sub}
          </p>
        )}
      </div>
    </div>
  );
}
