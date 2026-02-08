"use client";

import { useEffect, useState } from "react";
import {
  Bell,
  Mail,
  AlertTriangle,
  CheckCircle,
  Info,
  Loader2,
  Send,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Activity,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth-context";
import {
  apiGetNotifications,
  apiSendEmail,
  apiTestEmailConfig,
  type NotificationAlert,
  type EmailRequest,
} from "@/lib/api";

export default function NotificationsPage() {
  const { token, user } = useAuth();
  const [alerts, setAlerts] = useState<NotificationAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [emailConfig, setEmailConfig] = useState<{
    configured: boolean;
    status: string;
  } | null>(null);
  
  // Email form state
  const [emailForm, setEmailForm] = useState({
    to: "",
    subject: "",
    body: "",
  });
  const [sendingEmail, setSendingEmail] = useState(false);

  // Load alerts and email config
  const loadData = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const [alertsData, configData] = await Promise.all([
        apiGetNotifications(token).catch(() => []),
        apiTestEmailConfig(token).catch(() => ({ configured: false, status: "error" })),
      ]);
      setAlerts(alertsData);
      setEmailConfig(configData);
    } catch (error) {
      console.error("Failed to load notifications:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSendEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !emailForm.to || !emailForm.subject) return;

    setSendingEmail(true);
    try {
      const emailRequest: EmailRequest = {
        to: emailForm.to.split(",").map((e) => e.trim()),
        subject: emailForm.subject,
        body: emailForm.body,
      };
      await apiSendEmail(token, emailRequest);
      alert("✅ Email envoyé avec succès!");
      setEmailForm({ to: "", subject: "", body: "" });
    } catch (error) {
      console.error("Email send failed:", error);
      alert("❌ Échec de l'envoi de l'email");
    } finally {
      setSendingEmail(false);
    }
  };

  // Generate mock alerts for demo
  const mockAlerts: NotificationAlert[] = [
    {
      ticker: "BIAT",
      alert_type: "price_spike",
      message: "Prix en hausse de +5.2% en 1 heure",
      severity: "high",
      created_at: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      ticker: "SFBT",
      alert_type: "volume_spike",
      message: "Volume de transactions inhabituel (+300%)",
      severity: "medium",
      created_at: new Date(Date.now() - 7200000).toISOString(),
    },
    {
      ticker: "BNA",
      alert_type: "sentiment_change",
      message: "Sentiment passé de négatif à positif",
      severity: "low",
      created_at: new Date(Date.now() - 10800000).toISOString(),
    },
  ];

  const displayAlerts = alerts.length > 0 ? alerts : mockAlerts;

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "high":
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case "medium":
        return <Info className="h-5 w-5 text-yellow-500" />;
      default:
        return <CheckCircle className="h-5 w-5 text-green-500" />;
    }
  };

  const getAlertTypeIcon = (type: string) => {
    if (type.includes("price")) return <TrendingUp className="h-4 w-4" />;
    if (type.includes("volume")) return <Activity className="h-4 w-4" />;
    if (type.includes("sentiment")) return <TrendingDown className="h-4 w-4" />;
    return <Bell className="h-4 w-4" />;
  };

  return (
    <div className="p-6 pb-20 md:pb-6">
      <div className="space-y-6">
        <PageHeader
          title="🔔 Notifications & Alertes"
          description="Gérez vos alertes de marché et envoyez des notifications par email"
        >
          <Button onClick={loadData} disabled={loading} variant="outline">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Actualiser
          </Button>
        </PageHeader>

      {/* Email Configuration Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Configuration Email
          </CardTitle>
        </CardHeader>
        <CardContent>
          {emailConfig ? (
            <div className="flex items-center gap-3">
              {emailConfig.configured ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-sm text-muted-foreground">
                    Service email configuré et opérationnel
                  </span>
                </>
              ) : (
                <>
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  <span className="text-sm text-muted-foreground">
                    Gmail non configuré - Mode simulation activé
                  </span>
                </>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-3 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Vérification de la configuration...
            </div>
          )}
        </CardContent>
      </Card>

      {/* Alerts Feed */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Alertes Récentes
            </CardTitle>
            <Badge variant="outline">{displayAlerts.length} alertes</Badge>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : displayAlerts.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              Aucune alerte pour le moment
            </div>
          ) : (
            <div className="space-y-3">
              {displayAlerts.map((alert, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-4 p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                >
                  <div className="mt-0.5">{getSeverityIcon(alert.severity)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {getAlertTypeIcon(alert.alert_type)}
                      <Badge variant="secondary" className="text-xs font-mono">
                        {alert.ticker}
                      </Badge>
                      <Badge
                        variant={
                          alert.severity === "high"
                            ? "danger"
                            : alert.severity === "medium"
                            ? "warning"
                            : "muted"
                        }
                        className="text-xs"
                      >
                        {alert.severity}
                      </Badge>
                    </div>
                    <p className="text-sm font-medium mb-1">{alert.message}</p>
                    <p className="text-xs text-muted-foreground">
                      {alert.created_at
                        ? new Date(alert.created_at).toLocaleString("fr-FR")
                        : "Maintenant"}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Send Email Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Send className="h-5 w-5" />
            Envoyer un Email
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSendEmail} className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Destinataires (séparés par des virgules)
              </label>
              <Input
                type="text"
                placeholder="example@email.com, autre@email.com"
                value={emailForm.to}
                onChange={(e) =>
                  setEmailForm({ ...emailForm, to: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Sujet</label>
              <Input
                type="text"
                placeholder="Rapport de marché quotidien"
                value={emailForm.subject}
                onChange={(e) =>
                  setEmailForm({ ...emailForm, subject: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Message</label>
              <textarea
                className="w-full min-h-[120px] px-3 py-2 border border-border rounded-lg bg-card text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                placeholder="Votre message ici..."
                value={emailForm.body}
                onChange={(e) =>
                  setEmailForm({ ...emailForm, body: e.target.value })
                }
              />
            </div>
            <Button type="submit" disabled={sendingEmail}>
              {sendingEmail ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Envoi en cours...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Envoyer
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-500/10 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-red-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {displayAlerts.filter((a) => a.severity === "high").length}
                </p>
                <p className="text-xs text-muted-foreground">Alertes Critiques</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-500/10 rounded-lg">
                <Info className="h-5 w-5 text-yellow-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {displayAlerts.filter((a) => a.severity === "medium").length}
                </p>
                <p className="text-xs text-muted-foreground">Alertes Moyennes</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <CheckCircle className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {displayAlerts.filter((a) => a.severity === "low").length}
                </p>
                <p className="text-xs text-muted-foreground">Info</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      </div>
    </div>
  );
}
