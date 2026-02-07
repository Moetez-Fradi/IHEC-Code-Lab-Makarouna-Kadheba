import { API_URL } from "./config";

// ── Auth ──

export async function apiLogin(email: string, password: string) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message ?? "Échec de la connexion");
  }
  return res.json() as Promise<{
    access_token: string;
    user: { id: number; email: string; username: string };
  }>;
}

export async function apiSignup(email: string, username: string, password: string) {
  const res = await fetch(`${API_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message ?? "Échec de l'inscription");
  }
  return res.json() as Promise<{
    access_token: string;
    user: { id: number; email: string; username: string };
  }>;
}

export async function apiGetMe(token: string) {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Non autorisé");
  return res.json() as Promise<{ id: number; email: string; username: string }>;
}

// ── Market ──

async function authFetch<T>(path: string, token: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 401) {
    // Token expired — clear and redirect
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    throw new Error("Session expirée");
  }
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export interface MarketStock {
  id: number;
  code: string;
  valeur: string;
  seance: string;
  ouverture: number;
  cloture: number;
  plusHaut: number;
  plusBas: number;
  quantiteNegociee: number;
  capitaux: number;
  nbTransaction: number;
  groupe: number;
  change?: number;
  changePercent?: number;
}

export function apiGetOverview(token: string) {
  return authFetch<MarketStock[]>("/market/overview", token);
}

export function apiGetStocks(token: string) {
  return authFetch<{ code: string; valeur: string }[]>("/market/stocks", token);
}

export function apiGetHistory(token: string, code: string, days = 90) {
  return authFetch<MarketStock[]>(`/market/history/${encodeURIComponent(code)}?days=${days}`, token);
}

export function apiGetLatest(token: string) {
  return authFetch<MarketStock[]>("/market/latest", token);
}
