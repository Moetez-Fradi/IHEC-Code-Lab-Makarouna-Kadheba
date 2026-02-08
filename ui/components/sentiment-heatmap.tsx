"use client";

import { useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface SentimentScore {
  ticker: string;
  score: number;
  classification: "positive" | "negative" | "neutral";
  articleCount: number;
}

interface SentimentHeatmapProps {
  data: SentimentScore[];
  loading?: boolean;
  title?: string;
  subtitle?: string;
}

export function SentimentHeatmap({
  data,
  loading = false,
  title = "Sentiment Heatmap",
  subtitle,
}: SentimentHeatmapProps) {
  // Sort data by sentiment score (most positive first)
  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => b.score - a.score);
  }, [data]);

  // Calculate stats
  const stats = useMemo(() => {
    if (data.length === 0) return { positive: 0, negative: 0, neutral: 0, avgScore: 0 };
    
    const positive = data.filter((d) => d.classification === "positive").length;
    const negative = data.filter((d) => d.classification === "negative").length;
    const neutral = data.filter((d) => d.classification === "neutral").length;
    const avgScore = data.reduce((sum, d) => sum + d.score, 0) / data.length;
    
    return { positive, negative, neutral, avgScore };
  }, [data]);

  // Get color based on sentiment score
  const getColor = (score: number): string => {
    if (score > 0.4) return "rgb(34, 197, 94)"; // Green
    if (score > 0.2) return "rgb(134, 239, 172)"; // Light green
    if (score > 0.05) return "rgb(187, 247, 208)"; // Very light green
    if (score > -0.05) return "rgb(229, 231, 235)"; // Gray (neutral)
    if (score > -0.2) return "rgb(254, 202, 202)"; // Light red
    if (score > -0.4) return "rgb(252, 165, 165)"; // Red
    return "rgb(239, 68, 68)"; // Dark red
  };

  // Get background color with opacity
  const getBgColor = (score: number): string => {
    if (score > 0.4) return "rgba(34, 197, 94, 0.15)"; 
    if (score > 0.2) return "rgba(34, 197, 94, 0.1)"; 
    if (score > 0.05) return "rgba(34, 197, 94, 0.05)"; 
    if (score > -0.05) return "rgba(156, 163, 175, 0.05)"; 
    if (score > -0.2) return "rgba(239, 68, 68, 0.05)"; 
    if (score > -0.4) return "rgba(239, 68, 68, 0.1)"; 
    return "rgba(239, 68, 68, 0.15)";
  };

  // Get icon based on classification
  const getIcon = (classification: string) => {
    if (classification === "positive")
      return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (classification === "negative")
      return <TrendingDown className="h-4 w-4 text-red-600" />;
    return <Minus className="h-4 w-4 text-gray-400" />;
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-12">
            Aucune donnée de sentiment disponible. Lancez un scraping pour commencer.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{title}</CardTitle>
            {subtitle && (
              <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
            )}
          </div>
          <div className="flex gap-2">
            <Badge variant="success" className="gap-1">
              <TrendingUp className="h-3 w-3" />
              {stats.positive}
            </Badge>
            <Badge variant="muted" className="gap-1">
              <Minus className="h-3 w-3" />
              {stats.neutral}
            </Badge>
            <Badge variant="danger" className="gap-1">
              <TrendingDown className="h-3 w-3" />
              {stats.negative}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Market Average */}
        <div className="mb-6 p-4 rounded-lg bg-accent/50 border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Sentiment Moyen du Marché</p>
              <div className="flex items-center gap-2 mt-1">
                {getIcon(
                  stats.avgScore > 0.15
                    ? "positive"
                    : stats.avgScore < -0.15
                    ? "negative"
                    : "neutral"
                )}
                <span className="text-2xl font-bold">
                  {stats.avgScore > 0 ? "+" : ""}
                  {stats.avgScore.toFixed(3)}
                </span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">{data.length} actions</p>
              <p className="text-xs text-muted-foreground mt-1">
                {((stats.positive / data.length) * 100).toFixed(0)}% positif
              </p>
            </div>
          </div>
        </div>

        {/* Heatmap Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
          {sortedData.map((item) => (
            <div
              key={item.ticker}
              className="relative group cursor-pointer rounded-lg border transition-all hover:scale-105 hover:shadow-lg hover:z-10"
              style={{
                backgroundColor: getBgColor(item.score),
                borderColor: getColor(item.score),
                borderWidth: "2px",
              }}
            >
              <div className="p-3">
                {/* Ticker */}
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-sm font-mono">{item.ticker}</span>
                  {getIcon(item.classification)}
                </div>

                {/* Score */}
                <div
                  className="text-2xl font-bold mb-1"
                  style={{ color: getColor(item.score) }}
                >
                  {item.score > 0 ? "+" : ""}
                  {item.score.toFixed(2)}
                </div>

                {/* Article count */}
                <div className="text-xs text-muted-foreground">
                  {item.articleCount} article{item.articleCount > 1 ? "s" : ""}
                </div>

                {/* Classification badge */}
                <Badge
                  variant={
                    item.classification === "positive"
                      ? "success"
                      : item.classification === "negative"
                      ? "danger"
                      : "muted"
                  }
                  className="mt-2 text-xs w-full justify-center"
                >
                  {item.classification === "positive"
                    ? "Positif"
                    : item.classification === "negative"
                    ? "Négatif"
                    : "Neutre"}
                </Badge>
              </div>

              {/* Tooltip on hover */}
              <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block z-20">
                <div className="bg-popover text-popover-foreground px-3 py-2 rounded-lg shadow-lg border text-xs whitespace-nowrap">
                  <div className="font-bold mb-1">{item.ticker}</div>
                  <div>Score: {item.score.toFixed(3)}</div>
                  <div>Articles: {item.articleCount}</div>
                  <div>
                    Sentiment:{" "}
                    {item.classification === "positive"
                      ? "Positif"
                      : item.classification === "negative"
                      ? "Négatif"
                      : "Neutre"}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="mt-6 pt-6 border-t">
          <p className="text-sm font-semibold mb-3">Légende des Couleurs</p>
          <div className="flex flex-wrap gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded border"
                style={{ backgroundColor: "rgb(34, 197, 94)" }}
              />
              <span>&gt; +0.40 (Très positif)</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded border"
                style={{ backgroundColor: "rgb(134, 239, 172)" }}
              />
              <span>+0.20 à +0.40 (Positif)</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded border"
                style={{ backgroundColor: "rgb(229, 231, 235)" }}
              />
              <span>-0.05 à +0.05 (Neutre)</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded border"
                style={{ backgroundColor: "rgb(252, 165, 165)" }}
              />
              <span>-0.40 à -0.20 (Négatif)</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded border"
                style={{ backgroundColor: "rgb(239, 68, 68)" }}
              />
              <span>&lt; -0.40 (Très négatif)</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
