"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { TrendingUp, Eye, EyeOff } from "lucide-react";
import { apiSignup } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function SignupPage() {
  const router = useRouter();
  const auth = useAuth();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { access_token, user } = await apiSignup(email, username, password);
      auth.login(access_token, user);
      router.replace("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Échec de l'inscription");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center gap-3 justify-center mb-10">
          <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div className="leading-tight">
            <span className="text-lg font-semibold text-foreground tracking-tight">BVMT</span>
            <span className="block text-[11px] text-muted tracking-widest uppercase">Trading Assistant</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="email" className="block text-xs font-medium text-muted mb-1.5">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="vous@exemple.com"
              className="w-full px-3.5 py-2.5 rounded-lg bg-card border border-border text-sm text-foreground placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent transition"
            />
          </div>

          <div>
            <label htmlFor="username" className="block text-xs font-medium text-muted mb-1.5">
              Nom d&apos;utilisateur
            </label>
            <input
              id="username"
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="votrenom"
              className="w-full px-3.5 py-2.5 rounded-lg bg-card border border-border text-sm text-foreground placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent transition"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-xs font-medium text-muted mb-1.5">
              Mot de passe
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPw ? "text" : "password"}
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Min. 6 caractères"
                className="w-full px-3.5 py-2.5 rounded-lg bg-card border border-border text-sm text-foreground placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent transition pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPw(!showPw)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-foreground transition"
              >
                {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-lg">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-accent hover:bg-accent/90 text-white text-sm font-medium transition disabled:opacity-50"
          >
            {loading ? "Création..." : "Créer un compte"}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-muted">
          Déjà inscrit ?{" "}
          <Link href="/login" className="text-accent-light hover:underline">
            Se connecter
          </Link>
        </p>
      </div>
    </div>
  );
}
