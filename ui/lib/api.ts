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

// ── Forecast ──

export interface DayForecast {
  date: string;
  predicted_close: number;
  confidence_low: number;
  confidence_high: number;
  predicted_volume: number;
  liquidity_probability: number;
  liquidity_label: string;
}

export interface ForecastReport {
  stock_code: string;
  stock_name: string;
  forecast_from: string;
  horizon: number;
  model: string;
  daily_forecasts: DayForecast[];
  metrics: Record<string, { rmse: number; mae: number; mape: number; directional_accuracy: number }>;
  historical_close: { date: string; close: number; volume: number }[];
}

export function apiGetForecast(token: string, code: string, lookback?: number) {
  const params = lookback ? `&lookback=${lookback}` : "";
  return authFetch<ForecastReport>(`/forecast?code=${encodeURIComponent(code)}${params}`, token);
}

// ── Anomalies ──

export interface AnomalyDetail {
  SEANCE: string;
  OUVERTURE: number;
  CLOTURE: number;
  QUANTITE_NEGOCIEE: number;
  NB_TRANSACTION: number;
  CAPITAUX: number;
  volume_zscore: number;
  price_change_pct: number;
  isolation_score: number;
}

export interface Anomaly {
  date: string;
  types: string[];
  severity: number;
  details: AnomalyDetail;
}

export interface AnomalySummary {
  avg_severity: number;
  max_severity: number;
  type_counts: Record<string, number>;
  volume_anomalies: number;
  price_anomalies: number;
  pattern_anomalies: number;
}

export interface AnomalyReport {
  code: string;
  start: string;
  end: string;
  total_days: number;
  anomaly_days: number;
  anomalies: Anomaly[];
  summary: AnomalySummary;
}

export function apiGetAnomalies(token: string, code: string, start: string, end: string) {
  return authFetch<AnomalyReport>(
    `/anomalies?code=${encodeURIComponent(code)}&start=${start}&end=${end}`,
    token,
  );
}

// ── Portfolio ──

async function authPost<T>(path: string, token: string, body: object): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (res.status === 401) {
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

export interface PortfolioRecommendation {
  profile: string;
  weights: Record<string, number>;
  metrics: {
    sharpe?: number;
    sortino?: number;
    max_drawdown?: number;
    volatility?: number;
    annual_return?: number;
    [key: string]: number | undefined;
  };
  explanation: string;
}

export interface PortfolioSimulation {
  profile: string;
  initial_capital: number;
  final_value: number;
  roi: number;
  sharpe: number;
  sortino: number;
  max_drawdown: number;
  volatility: number;
  n_days: number;
  daily_values: number[];
}

export interface PortfolioStressTest {
  pre_stress: { value: number };
  post_stress: { value: number };
  impact: number;
}

export interface PortfolioSnapshot {
  cash: number;
  value: number;
  weights: Record<string, number>;
  n_transactions: number;
}

export interface MacroData {
  data: Record<string, number | string>;
}

export function apiPortfolioRecommend(token: string, profile: string) {
  return authPost<PortfolioRecommendation>("/portfolio/recommend", token, { profile });
}

export function apiPortfolioSimulate(
  token: string,
  profile: string,
  capital?: number,
  days?: number,
) {
  return authPost<PortfolioSimulation>("/portfolio/simulate", token, {
    profile,
    capital,
    days,
  });
}

export function apiPortfolioStressTest(
  token: string,
  stressType: string,
  intensity: number,
) {
  return authPost<PortfolioStressTest>("/portfolio/stress-test", token, {
    stress_type: stressType,
    intensity,
  });
}

export function apiPortfolioSnapshot(token: string) {
  return authFetch<PortfolioSnapshot>("/portfolio/snapshot", token);
}

export function apiPortfolioMacro(token: string) {
  return authFetch<MacroData>("/portfolio/macro", token);
}

export function apiPortfolioTrain(token: string, timesteps?: number, adversarial?: boolean) {
  return authPost<{ mean_reward: number; mean_value: number }>("/portfolio/train", token, {
    timesteps,
    adversarial,
  });
}
