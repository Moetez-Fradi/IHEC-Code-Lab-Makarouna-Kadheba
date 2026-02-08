"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Search, Twitter, MessageSquare, AlertTriangle } from "lucide-react";
import { Input } from "@/components/ui/input";

interface SocialSentimentData {
  ticker: string;
  total_posts: number;
  sentiment_summary: {
    overall_sentiment: "positive" | "negative" | "neutral";
    avg_score: number;
    positive_posts: number;
    negative_posts: number;
    neutral_posts: number;
  };
  comparison: {
    social_media_sentiment: number;
    official_news_sentiment: number | null;
    delta: number | null;
    interpretation: string | null;
  };
  tunizi_stats: {
    posts_with_tunizi: number;
    percentage: number;
  };
  platforms: Record<string, { count: number }>;
}

interface SocialMediaSentimentProps {
  token: string;
  apiUrl: string;
}

export function SocialMediaSentiment({ token, apiUrl }: SocialMediaSentimentProps) {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<SocialSentimentData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!ticker.trim()) return;

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const res = await fetch(
        `${apiUrl}/sentiment/search-social-media?ticker=${encodeURIComponent(ticker.toUpperCase())}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!res.ok) {
        throw new Error("Échec de la recherche");
      }

      const result = await res.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.15) return "text-green-500";
    if (score < -0.15) return "text-red-500";
    return "text-gray-400";
  };

  const getSentimentBadge = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return <Badge variant="success">Positif</Badge>;
      case "negative":
        return <Badge variant="danger">Négatif</Badge>;
      default:
        return <Badge variant="muted">Neutre</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Twitter className="h-5 w-5 text-blue-400" />
          🐦 Sentiment des Réseaux Sociaux
        </CardTitle>
        <p className="text-sm text-muted-foreground mt-1">
          Recherche sur Twitter, Reddit r/tunisia, Facebook et Tunisia-Sat forums
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search Input */}
        <div className="flex gap-2">
          <Input
            placeholder="Ticker (ex: SFBT, BIAT, BNA)"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="font-mono"
          />
          <Button onClick={handleSearch} disabled={loading || !ticker.trim()}>
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            {loading ? "Recherche..." : "Rechercher"}
          </Button>
        </div>

        {/* Error */}
        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
            ❌ {error}
          </div>
        )}

        {/* Results */}
        {data && (
          <div className="space-y-4">
            {/* No posts found */}
            {data.total_posts === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                Aucune discussion trouvée pour {data.ticker} sur les 7 derniers jours
              </div>
            ) : (
              <>
                {/* Summary Cards */}
                <div className="grid md:grid-cols-3 gap-4">
                  {/* Posts Count */}
                  <Card className="bg-card-hover">
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <MessageSquare className="h-8 w-8 mx-auto mb-2 text-blue-400" />
                        <div className="text-3xl font-bold">{data.total_posts}</div>
                        <div className="text-sm text-muted-foreground">Posts trouvés</div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Social Sentiment */}
                  <Card className="bg-card-hover">
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <div className={`text-3xl font-bold ${getSentimentColor(data.sentiment_summary.avg_score)}`}>
                          {data.sentiment_summary.avg_score > 0 ? "+" : ""}
                          {data.sentiment_summary.avg_score.toFixed(2)}
                        </div>
                        <div className="mt-2">
                          {getSentimentBadge(data.sentiment_summary.overall_sentiment)}
                        </div>
                        <div className="text-sm text-muted-foreground mt-1">Sentiment Social</div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Tunizi Detection */}
                  <Card className="bg-card-hover">
                    <CardContent className="pt-6">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-purple-400">
                          {data.tunizi_stats.percentage.toFixed(0)}%
                        </div>
                        <div className="text-sm text-muted-foreground mt-2">
                          {data.tunizi_stats.posts_with_tunizi} posts en Tunizi
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Platforms Breakdown */}
                <Card className="bg-card-hover">
                  <CardHeader>
                    <CardTitle className="text-sm">Posts par Plateforme</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {Object.entries(data.platforms).map(([platform, info]) => (
                        <div key={platform} className="text-center p-3 bg-background rounded-lg border">
                          <div className="text-lg font-bold">{info.count}</div>
                          <div className="text-xs text-muted-foreground capitalize">{platform}</div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Sentiment Gap Analysis */}
                {data.comparison.official_news_sentiment !== null && (
                  <Card className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 border-purple-500/20">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-sm">
                        <AlertTriangle className="h-4 w-4 text-yellow-400" />
                        Analyse de Divergence
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Réseaux Sociaux</div>
                          <div className={`text-2xl font-bold ${getSentimentColor(data.comparison.social_media_sentiment)}`}>
                            {data.comparison.social_media_sentiment > 0 ? "+" : ""}
                            {data.comparison.social_media_sentiment.toFixed(3)}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Actualités Officielles</div>
                          <div className={`text-2xl font-bold ${getSentimentColor(data.comparison.official_news_sentiment)}`}>
                            {data.comparison.official_news_sentiment > 0 ? "+" : ""}
                            {data.comparison.official_news_sentiment.toFixed(3)}
                          </div>
                        </div>
                      </div>

                      {data.comparison.delta !== null && Math.abs(data.comparison.delta) > 0.1 && (
                        <div className="pt-3 border-t border-purple-500/20">
                          <div className="text-sm">
                            <strong>Écart:</strong> {data.comparison.delta > 0 ? "+" : ""}
                            {data.comparison.delta.toFixed(3)}
                          </div>
                          <div className="text-sm text-muted-foreground mt-1">
                            {data.comparison.interpretation}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Sentiment Distribution */}
                <Card className="bg-card-hover">
                  <CardHeader>
                    <CardTitle className="text-sm">Distribution des Sentiments</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-green-400">Positif</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 h-2 bg-background rounded-full overflow-hidden">
                            <div
                              className="h-full bg-green-500"
                              style={{
                                width: `${(data.sentiment_summary.positive_posts / data.total_posts) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="text-sm font-mono w-12 text-right">
                            {data.sentiment_summary.positive_posts}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-400">Neutre</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 h-2 bg-background rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gray-500"
                              style={{
                                width: `${(data.sentiment_summary.neutral_posts / data.total_posts) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="text-sm font-mono w-12 text-right">
                            {data.sentiment_summary.neutral_posts}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-red-400">Négatif</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 h-2 bg-background rounded-full overflow-hidden">
                            <div
                              className="h-full bg-red-500"
                              style={{
                                width: `${(data.sentiment_summary.negative_posts / data.total_posts) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="text-sm font-mono w-12 text-right">
                            {data.sentiment_summary.negative_posts}
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        )}

        {/* Info Box */}
        {!data && !loading && (
          <div className="text-sm text-muted-foreground border border-border/50 rounded-lg p-4">
            <p className="mb-2">
              💡 Cette fonctionnalité recherche les discussions sur les réseaux sociaux
              où les Tunisiens discutent réellement des actions:
            </p>
            <ul className="space-y-1 ml-4">
              <li>• Twitter/X (#Bourse, #BVMT)</li>
              <li>• Reddit r/tunisia (investissement)</li>
              <li>• Groupes Facebook (finance tunisienne)</li>
              <li>• Forums Tunisia-Sat (section BVMT)</li>
            </ul>
            <p className="mt-2 text-xs">
              ⚡ Recherche en temps réel avec analyse Tunizi/Arabizi. Temps de réponse: ~30 secondes.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
