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

// ── Sentiment Analysis ──

export interface SentimentData {
  ticker: string;
  date: string;
  avg_score: number;
  article_count: number;
  classification: 'positive' | 'negative' | 'neutral';
}

export interface SentimentArticle {
  id: number;
  source: string;
  title: string;
  url?: string;
  sentiment: string;
  score: number;
  ticker?: string;
  created_at: string;
}

export function apiGetSentiment(token: string, ticker: string, days: number = 30) {
  return authFetch<SentimentData[]>(
    `/sentiment/daily/${encodeURIComponent(ticker)}?days=${days}`,
    token,
  );
}

export function apiGetSentimentArticles(token: string, ticker?: string, limit: number = 20) {
  const tickerParam = ticker ? `ticker=${encodeURIComponent(ticker)}&` : '';
  return authFetch<SentimentArticle[]>(
    `/sentiment/articles?${tickerParam}limit=${limit}`,
    token,
  );
}

export function apiScrapeSentiment(token: string) {
  return authFetch<{ message: string; articles_scraped: number }>(
    `/sentiment/scrape`,
    token,
  );
}

// ── Portfolio Management ──

export interface PortfolioWeights {
  [ticker: string]: number;
}

export interface PortfolioMetrics {
  roi: number;
  sharpe: number;
  sortino: number;
  max_drawdown: number;
  volatility: number;
  calmar_ratio: number;
}

export interface PortfolioRecommendation {
  profile: string;
  weights: PortfolioWeights;
  metrics: PortfolioMetrics;
  explanation: string;
}

export interface PortfolioSimulation {
  profile: string;
  initial_capital: number;
  final_value: number;
  total_return: number;
  timeline: Array<{
    date: string;
    value: number;
  }>;
  metrics: PortfolioMetrics;
}

export function apiGetPortfolioRecommendation(
  token: string,
  profile: 'conservateur' | 'modere' | 'agressif'
) {
  return authFetch<PortfolioRecommendation>(
    `/portfolio/recommend`,
    token,
  ).then(data => 
    fetch(`${API_URL}/portfolio/recommend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ profile }),
    }).then(res => res.json())
  );
}

export function apiSimulatePortfolio(
  token: string,
  profile: 'conservateur' | 'modere' | 'agressif',
  capital: number = 10000,
  days: number = 90
) {
  return fetch(`${API_URL}/portfolio/simulate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ profile, capital, days }),
  }).then(res => res.json()) as Promise<PortfolioSimulation>;
}

export function apiStressTestPortfolio(
  token: string,
  stress_type: 'sector_crash' | 'interest_rate_spike' | 'currency_depreciation',
  intensity: number = 0.1
) {
  return fetch(`${API_URL}/portfolio/stress-test`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ stress_type, intensity }),
  }).then(res => res.json());
}

export function apiGetMacroData(token: string) {
  return authFetch<any>(`/portfolio/macro`, token);
}

// ── Predictions ──

export interface PredictionData {
  id: number;
  stock_id: number;
  target_date: string;
  predicted_price: number;
  lower_bound?: number;
  upper_bound?: number;
  liquidity_class?: string;
  liquidity_probability?: number;
  confidence: number;
}

export function apiGetPredictions(token: string, ticker: string) {
  return authFetch<PredictionData[]>(
    `/predictions/${encodeURIComponent(ticker)}`,
    token,
  );
}
