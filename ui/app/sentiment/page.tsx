"use client";

import { useEffect, useState, Suspense } from "react";
import { Loader2, Sparkles, RefreshCw, MessageSquare } from "lucide-react";
import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { SentimentHeatmap } from "@/components/sentiment-heatmap";
import { SocialMediaSentiment } from "@/components/social-media-sentiment";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth-context";
import { API_URL } from "@/lib/config";
import {
  apiGetAllSentiments,
  apiScrapeSentiment,
  apiGetSentimentArticles,
  type SentimentArticle,
} from "@/lib/api";

interface SentimentScore {
  ticker: string;
  score: number;
  classification: "positive" | "negative" | "neutral";
  articleCount: number;
}

function SentimentPageContent() {
  const { token } = useAuth();
  const [sentiments, setSentiments] = useState<SentimentScore[]>([]);
  const [articles, setArticles] = useState<SentimentArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  // Load sentiment data
  const loadSentiments = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const data = await apiGetAllSentiments(token);
      
      // Transform API data to heatmap format
      const heatmapData: SentimentScore[] = data.tickers.map((t) => ({
        ticker: t.ticker,
        score: t.avg_score,
        classification: t.classification,
        articleCount: t.article_count,
      }));
      
      setSentiments(heatmapData);
      setLastUpdate(data.date);
      
      // Also load recent articles
      const recentArticles = await apiGetSentimentArticles(token, undefined, 10);
      setArticles(recentArticles);
    } catch (error) {
      console.error("Failed to load sentiments:", error);
    } finally {
      setLoading(false);
    }
  };

  // Trigger scraping
  const handleScrape = async () => {
    if (!token) return;
    
    setScraping(true);
    try {
      const result = await apiScrapeSentiment(token);
      alert(`✅ Scraping terminé: ${result.articles_scraped} articles analysés`);
      // Reload sentiments after scraping
      await loadSentiments();
    } catch (error) {
      console.error("Scraping failed:", error);
      alert("❌ Échec du scraping");
    } finally {
      setScraping(false);
    }
  };

  useEffect(() => {
    loadSentiments();
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-6">
      <PageHeader
        title="🇹🇳 Analyse des Sentiments"
        description="Sentiment en temps réel sur la BVMT avec analyse Tunizi/Arabizi et scraping social media"
        actions={
          <div className="flex gap-2">
            <Button
              onClick={loadSentiments}
              disabled={loading}
              variant="outline"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Actualiser
            </Button>
            <Button
              onClick={handleScrape}
              disabled={scraping}
            >
              <Sparkles className={`h-4 w-4 mr-2 ${scraping ? 'animate-pulse' : ''}`} />
              {scraping ? "Scraping..." : "Lancer Scraping"}
            </Button>
          </div>
        }
      />

      {/* Heatmap */}
      <SentimentHeatmap
        data={sentiments}
        loading={loading}
        title="📊 Heatmap des Sentiments - Toutes les Actions"
        subtitle={
          lastUpdate
            ? `Dernière mise à jour: ${new Date(lastUpdate).toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
              })}`
            : undefined
        }
      />

      {/* Social Media Sentiment Search */}
      {token && <SocialMediaSentiment token={token} apiUrl={API_URL} />}

      {/* Recent Articles */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Articles Récents
            </CardTitle>
            <Badge variant="outline">{articles.length} articles</Badge>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : articles.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              Aucun article disponible. Lancez un scraping pour analyser les dernières actualités.
            </div>
          ) : (
            <div className="space-y-3">
              {articles.map((article) => (
                <div
                  key={article.id}
                  className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline" className="text-xs">
                          {article.source}
                        </Badge>
                        {article.ticker && (
                          <Badge variant="secondary" className="text-xs font-mono">
                            {article.ticker}
                          </Badge>
                        )}
                        <Badge
                          variant={
                            article.sentiment === "positive"
                              ? "success"
                              : article.sentiment === "negative"
                              ? "danger"
                              : "muted"
                          }
                          className="text-xs"
                        >
                          {article.sentiment}
                        </Badge>
                      </div>
                      <h3 className="font-semibold text-sm mb-1 line-clamp-2">
                        {article.title}
                      </h3>
                      {article.url && (
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-primary hover:underline"
                        >
                          Voir l'article →
                        </a>
                      )}
                    </div>
                    <div className="text-right shrink-0">
                      <div
                        className="text-2xl font-bold"
                        style={{
                          color:
                            article.score > 0.15
                              ? "rgb(34, 197, 94)"
                              : article.score < -0.15
                              ? "rgb(239, 68, 68)"
                              : "rgb(156, 163, 175)",
                        }}
                      >
                        {article.score > 0 ? "+" : ""}
                        {article.score.toFixed(2)}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {new Date(article.created_at).toLocaleDateString('fr-FR', {
                          day: 'numeric',
                          month: 'short',
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* K.O. Features Info */}
      <Card className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20 border-purple-200 dark:border-purple-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            🇹🇳 Avantage Compétitif - Analyse Tunizi
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">✨ Tunizi/Arabizi NLP</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• 50+ termes slang financiers ("ti7", "tla3", "yaasr")</li>
                <li>• Normalisation Arabizi (2→aa, 7→h, 9→q)</li>
                <li>• Surnoms d'entreprises ("la bière"→SFBT)</li>
                <li>• Scoring hybride: 60% Tunizi + 40% Gemini</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">🐦 Social Media Integration</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Twitter/X (hashtags #Bourse, #BVMT)</li>
                <li>• Reddit r/tunisia (discussions investissement)</li>
                <li>• Facebook (groupes finance tunisiens)</li>
                <li>• Tunisia-Sat forums (section BVMT)</li>
              </ul>
            </div>
          </div>
          <div className="pt-4 border-t border-purple-200 dark:border-purple-800">
            <p className="text-sm text-muted-foreground">
              💡 <strong>Insight clé:</strong> La heatmap compare le sentiment des médias officiels
              (IlBoursa, Tustex) avec le sentiment retail des réseaux sociaux. Les divergences
              importantes (&gt;0.3) peuvent signaler des opportunités ou des risques avant qu'ils
              n'apparaissent dans les actualités officielles.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function SentimentPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      }
    >
      <SentimentPageContent />
    </Suspense>
  );
}
