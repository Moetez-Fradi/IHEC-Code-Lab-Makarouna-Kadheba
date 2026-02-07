// ────────────────────────────────────────
// Mock data for the entire dashboard
// Replace with real API calls when backend is ready
// ────────────────────────────────────────

/* ── helpers ── */
function rand(min: number, max: number) {
  return Math.round((Math.random() * (max - min) + min) * 100) / 100;
}

function randInt(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/* ── TUNINDEX history (60 trading days) ── */
export function generateTunindexHistory(days = 60) {
  const data: { date: string; value: number }[] = [];
  let v = 9180;
  const now = new Date();
  for (let i = days; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    if (d.getDay() === 0 || d.getDay() === 6) continue;
    v += rand(-40, 45);
    data.push({ date: d.toISOString().slice(0, 10), value: Math.round(v * 100) / 100 });
  }
  return data;
}

/* ── Stock list ── */
export interface Stock {
  ticker: string;
  name: string;
  sector: string;
  price: number;
  change: number;      // % daily
  volume: number;
  marketCap: number;    // in millions TND
  sentiment: "positive" | "negative" | "neutral";
  sentimentScore: number; // -1 to 1
  recommendation: "buy" | "sell" | "hold";
}

const TICKERS: [string, string, string][] = [
  ["BIAT", "Banque Internationale Arabe de Tunisie", "Banques"],
  ["BNA", "Banque Nationale Agricole", "Banques"],
  ["STB", "Société Tunisienne de Banque", "Banques"],
  ["SFBT", "Société de Fabrication des Boissons de Tunisie", "Agroalimentaire"],
  ["PGH", "Poulina Group Holding", "Holdings"],
  ["TLNET", "Telnet Holding", "Technologie"],
  ["OTH", "One Tech Holding", "Technologie"],
  ["SAH", "SAH Lilas", "Industrie"],
  ["SOTET", "Société Tunisienne d'Entreprises de Télécommunications", "Télécoms"],
  ["ARTES", "ARTES", "Distribution"],
  ["STAR", "Société Tunisienne d'Assurances et de Réassurances", "Assurances"],
  ["TPR", "TPR", "Immobilier"],
  ["UADH", "Universal Auto Distributeur Holding", "Distribution"],
  ["ATB", "Arab Tunisian Bank", "Banques"],
  ["BH", "Banque de l'Habitat", "Banques"],
  ["WIFAK", "Wifak International Bank", "Banques"],
  ["CITY", "City Cars", "Distribution"],
  ["ENNAKL", "Ennakl Automobiles", "Distribution"],
  ["DELICE", "Délice Holding", "Agroalimentaire"],
  ["MPBS", "Moderne Packaging & Business Services", "Industrie"],
];

export function generateStocks(): Stock[] {
  const sentiments: Stock["sentiment"][] = ["positive", "negative", "neutral"];
  const recs: Stock["recommendation"][] = ["buy", "sell", "hold"];
  return TICKERS.map(([ticker, name, sector]) => {
    const sentiment = sentiments[randInt(0, 2)];
    return {
      ticker,
      name,
      sector,
      price: rand(5, 180),
      change: rand(-6, 7),
      volume: randInt(5000, 800000),
      marketCap: rand(50, 4500),
      sentiment,
      sentimentScore: sentiment === "positive" ? rand(0.2, 1) : sentiment === "negative" ? rand(-1, -0.2) : rand(-0.2, 0.2),
      recommendation: recs[randInt(0, 2)],
    };
  });
}

/* ── Price history per stock ── */
export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export function generatePriceHistory(basePrice: number, days = 90): PricePoint[] {
  const data: PricePoint[] = [];
  let c = basePrice;
  const now = new Date();
  for (let i = days; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    if (d.getDay() === 0 || d.getDay() === 6) continue;
    const move = rand(-2, 2.2);
    const open = c;
    c = Math.max(1, c + move);
    const high = Math.max(open, c) + rand(0, 1.5);
    const low = Math.min(open, c) - rand(0, 1.5);
    data.push({
      date: d.toISOString().slice(0, 10),
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(Math.max(0.5, low) * 100) / 100,
      close: Math.round(c * 100) / 100,
      volume: randInt(5000, 500000),
    });
  }
  return data;
}

/* ── Forecast (5 days ahead) ── */
export interface ForecastPoint {
  date: string;
  predicted: number;
  upperBound: number;
  lowerBound: number;
}

export function generateForecast(lastPrice: number): ForecastPoint[] {
  const pts: ForecastPoint[] = [];
  let p = lastPrice;
  const now = new Date();
  let added = 0;
  let offset = 1;
  while (added < 5) {
    const d = new Date(now);
    d.setDate(d.getDate() + offset);
    offset++;
    if (d.getDay() === 0 || d.getDay() === 6) continue;
    p += rand(-1.5, 2);
    const spread = rand(1, 3) * (1 + added * 0.3);
    pts.push({
      date: d.toISOString().slice(0, 10),
      predicted: Math.round(p * 100) / 100,
      upperBound: Math.round((p + spread) * 100) / 100,
      lowerBound: Math.round(Math.max(0.5, p - spread) * 100) / 100,
    });
    added++;
  }
  return pts;
}

/* ── RSI & MACD (simplified) ── */
export function generateRSI(prices: PricePoint[]) {
  return prices.map((p) => ({
    date: p.date,
    rsi: rand(20, 80),
  }));
}

export function generateMACD(prices: PricePoint[]) {
  return prices.map((p) => ({
    date: p.date,
    macd: rand(-2, 2),
    signal: rand(-1.5, 1.5),
    histogram: rand(-1, 1),
  }));
}

/* ── Sentiment timeline ── */
export interface SentimentEntry {
  date: string;
  score: number;
  articles: number;
  source: string;
}

export function generateSentimentTimeline(days = 30): SentimentEntry[] {
  const sources = ["TAP", "Business News", "L'Économiste Maghrébin", "Leaders", "Webmanagercenter"];
  const data: SentimentEntry[] = [];
  const now = new Date();
  for (let i = days; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    if (d.getDay() === 0 || d.getDay() === 6) continue;
    data.push({
      date: d.toISOString().slice(0, 10),
      score: rand(-1, 1),
      articles: randInt(1, 15),
      source: sources[randInt(0, sources.length - 1)],
    });
  }
  return data;
}

/* ── Anomalies / Alerts ── */
export type AlertSeverity = "critical" | "warning" | "info";
export type AlertType = "volume_spike" | "price_anomaly" | "suspicious_pattern" | "liquidity_drop";

export interface Alert {
  id: string;
  timestamp: string;
  ticker: string;
  type: AlertType;
  severity: AlertSeverity;
  title: string;
  description: string;
  value: number;
  threshold: number;
  acknowledged: boolean;
}

const ALERT_TEMPLATES: { type: AlertType; title: string; desc: (t: string, v: number, th: number) => string }[] = [
  { type: "volume_spike", title: "Pic de volume détecté", desc: (t, v, th) => `Le volume de ${t} a atteint ${v.toLocaleString()} — ${Math.round(v / th)}× la moyenne.` },
  { type: "price_anomaly", title: "Variation anormale de prix", desc: (t, v) => `${t} a varié de ${v > 0 ? "+" : ""}${v.toFixed(2)}% en moins d'une heure sans actualité associée.` },
  { type: "suspicious_pattern", title: "Pattern d'ordres suspect", desc: (t) => `Séquence d'ordres inhabituels détectée sur ${t} — possible manipulation.` },
  { type: "liquidity_drop", title: "Chute de liquidité", desc: (t) => `Liquidité de ${t} en forte baisse — risque d'exécution.` },
];

export function generateAlerts(count = 25): Alert[] {
  const alerts: Alert[] = [];
  const tickers = TICKERS.map((t) => t[0]);
  const severities: AlertSeverity[] = ["critical", "warning", "info"];
  const now = Date.now();
  for (let i = 0; i < count; i++) {
    const tmpl = ALERT_TEMPLATES[randInt(0, ALERT_TEMPLATES.length - 1)];
    const ticker = tickers[randInt(0, tickers.length - 1)];
    const v = tmpl.type === "volume_spike" ? randInt(200000, 1500000) : rand(-8, 8);
    const th = tmpl.type === "volume_spike" ? randInt(30000, 80000) : 5;
    const ts = new Date(now - randInt(0, 7 * 24 * 3600 * 1000));
    alerts.push({
      id: `ALR-${String(i + 1).padStart(4, "0")}`,
      timestamp: ts.toISOString(),
      ticker,
      type: tmpl.type,
      severity: severities[randInt(0, 2)],
      title: tmpl.title,
      description: tmpl.desc(ticker, v, th),
      value: v,
      threshold: th,
      acknowledged: Math.random() > 0.7,
    });
  }
  return alerts.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

/* ── Portfolio ── */
export type RiskProfile = "conservateur" | "modéré" | "agressif";

export interface Position {
  ticker: string;
  name: string;
  shares: number;
  avgCost: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  weight: number;
  sector: string;
}

export interface PortfolioSummary {
  totalValue: number;
  totalCost: number;
  pnl: number;
  pnlPercent: number;
  roi: number;
  sharpe: number;
  maxDrawdown: number;
  riskProfile: RiskProfile;
  positions: Position[];
}

export function generatePortfolio(): PortfolioSummary {
  const selected = TICKERS.slice(0, randInt(5, 10));
  let totalValue = 0;
  let totalCost = 0;
  const positions: Position[] = selected.map(([ticker, name, sector]) => {
    const shares = randInt(10, 500);
    const avgCost = rand(8, 150);
    const currentPrice = avgCost + rand(-15, 25);
    const cost = shares * avgCost;
    const value = shares * currentPrice;
    totalCost += cost;
    totalValue += value;
    return {
      ticker,
      name,
      shares,
      avgCost: Math.round(avgCost * 100) / 100,
      currentPrice: Math.round(currentPrice * 100) / 100,
      pnl: Math.round((value - cost) * 100) / 100,
      pnlPercent: Math.round(((value - cost) / cost) * 10000) / 100,
      weight: 0,
      sector,
    };
  });
  positions.forEach((p) => {
    p.weight = Math.round((p.shares * p.currentPrice / totalValue) * 10000) / 100;
  });
  const pnl = totalValue - totalCost;
  return {
    totalValue: Math.round(totalValue * 100) / 100,
    totalCost: Math.round(totalCost * 100) / 100,
    pnl: Math.round(pnl * 100) / 100,
    pnlPercent: Math.round((pnl / totalCost) * 10000) / 100,
    roi: Math.round((pnl / totalCost) * 10000) / 100,
    sharpe: rand(0.3, 2.5),
    maxDrawdown: rand(-25, -3),
    riskProfile: (["conservateur", "modéré", "agressif"] as RiskProfile[])[randInt(0, 2)],
    positions,
  };
}

/* ── News feed ── */
export interface NewsItem {
  id: string;
  title: string;
  source: string;
  date: string;
  sentiment: "positive" | "negative" | "neutral";
  tickers: string[];
  summary: string;
}

export function generateNews(count = 12): NewsItem[] {
  const headlines = [
    { title: "BIAT annonce des résultats record pour le T4", sentiment: "positive" as const, tickers: ["BIAT"] },
    { title: "Le TUNINDEX franchit un nouveau seuil", sentiment: "positive" as const, tickers: [] },
    { title: "Pression vendeuse sur STB après les rumeurs de restructuration", sentiment: "negative" as const, tickers: ["STB"] },
    { title: "SFBT : dividende en hausse de 15%", sentiment: "positive" as const, tickers: ["SFBT"] },
    { title: "PGH diversifie ses investissements en Afrique", sentiment: "positive" as const, tickers: ["PGH"] },
    { title: "Telnet Holding signe un contrat spatial majeur", sentiment: "positive" as const, tickers: ["TLNET"] },
    { title: "Le CMF lance une enquête sur les transactions suspectes", sentiment: "negative" as const, tickers: [] },
    { title: "OTH : recul du CA au S1 2026", sentiment: "negative" as const, tickers: ["OTH"] },
    { title: "Le dinar tunisien en légère dépréciation", sentiment: "neutral" as const, tickers: [] },
    { title: "ARTES : résultats annuels conformes aux attentes", sentiment: "neutral" as const, tickers: ["ARTES"] },
    { title: "SAH Lilas renforce sa présence en Libye", sentiment: "positive" as const, tickers: ["SAH"] },
    { title: "Forte activité sur les valeurs bancaires cette semaine", sentiment: "neutral" as const, tickers: ["BIAT", "BNA", "ATB"] },
    { title: "CITY Cars enregistre une baisse de 8% des ventes", sentiment: "negative" as const, tickers: ["CITY"] },
    { title: "BH Banque : augmentation de capital approuvée", sentiment: "neutral" as const, tickers: ["BH"] },
    { title: "Délice Holding dépasse les prévisions des analystes", sentiment: "positive" as const, tickers: ["DELICE"] },
  ];
  const sources = ["TAP", "Business News", "L'Économiste Maghrébin", "Leaders", "Webmanagercenter"];
  const now = Date.now();
  return Array.from({ length: Math.min(count, headlines.length) }, (_, i) => {
    const h = headlines[i];
    const ts = new Date(now - randInt(0, 5 * 24 * 3600 * 1000));
    return {
      id: `NEWS-${i + 1}`,
      ...h,
      source: sources[randInt(0, sources.length - 1)],
      date: ts.toISOString(),
      summary: `Résumé de l'article : ${h.title.toLowerCase()}.`,
    };
  });
}
