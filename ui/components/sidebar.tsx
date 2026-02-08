"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  LineChart,
  Briefcase,
  ShieldAlert,
  TrendingUp,
  BrainCircuit,
  LogOut,
  MessageSquare,
  Bell,
  FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";
import { ThemeToggle } from "@/components/theme-toggle";

const NAV = [
  { href: "/", label: "Marché", icon: BarChart3 },
  { href: "/sentiment", label: "Sentiment", icon: MessageSquare },
  { href: "/analyse", label: "Analyse", icon: LineChart },
  { href: "/prevision", label: "Prévision", icon: BrainCircuit },
  { href: "/portefeuille", label: "Portefeuille", icon: Briefcase },
  { href: "/surveillance", label: "Surveillance", icon: ShieldAlert },
  { href: "/notifications", label: "Alertes", icon: Bell },
  { href: "/reports", label: "Rapports", icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="hidden md:flex flex-col w-[220px] border-r border-border bg-sidebar shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 h-16 border-b border-border">
        <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
          <TrendingUp className="w-4 h-4 text-white" />
        </div>
        <div className="leading-tight">
          <span className="text-sm font-semibold text-foreground tracking-tight">BVMT</span>
          <span className="block text-[10px] text-muted tracking-widest uppercase">Trading Assistant</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-3 space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                active
                  ? "bg-accent/10 text-accent-light"
                  : "text-muted hover:text-foreground hover:bg-card-hover"
              )}
            >
              <Icon className="w-[18px] h-[18px]" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-border space-y-3">
        {user && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center text-xs font-semibold text-accent-light">
                {user.username.slice(0, 1).toUpperCase()}
              </div>
              <span className="text-xs text-foreground font-medium truncate max-w-[100px]">{user.username}</span>
            </div>
            <div className="flex items-center gap-1">
              <ThemeToggle />
              <button onClick={logout} className="text-muted hover:text-foreground transition-colors p-2" title="Se déconnecter">
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
        <div>
          <p className="text-[10px] text-muted leading-relaxed">
            IHEC CodeLab 2.0
          </p>
          <p className="text-[10px] text-zinc-600">
            v0.2.0 — Données réelles BVMT
          </p>
        </div>
      </div>
    </aside>
  );
}
