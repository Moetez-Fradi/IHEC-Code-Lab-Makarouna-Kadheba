"""LLM interpreter — translates SHAP output into plain language."""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_PROMPT = """Tu es un conseiller financier IA spécialisé dans le marché tunisien (BVMT).

## Contexte — sources de données utilisées
• Données macroéconomiques réelles : Banque Mondiale (PIB, inflation, chômage),
  FMI (dette publique, balance courante) et BCT (taux directeur, TMM).
• Cours boursiers historiques des sociétés cotées à la BVMT.
• Un agent RL (PPO) entraîné sur ces données pour optimiser le portefeuille.
• Analyse SHAP (SHapley Additive Explanations) pour expliquer les décisions.

## Profil utilisateur
{profile_desc}

## Résultats SHAP (nom → impact)
{features}

## Poids recommandés
{weights}

## Métriques du portefeuille
{metrics}

## Consignes
Rédige une explication claire de 4 à 6 phrases en français, destinée
à un investisseur non technique. Explique :
1. Pourquoi le modèle recommande cette répartition pour CE profil de risque.
2. Quels facteurs macroéconomiques / de marché ont le plus influencé la décision.
3. Comment l'utilisateur peut bénéficier de cette recommandation.
"""


def interpret(
    shap_result: dict,
    weights: dict,
    profile_desc: str = "",
    metrics: dict | None = None,
) -> str:
    if not settings.OPENROUTER_API_KEY:
        return _fallback(shap_result, profile_desc)

    features_str = "\n".join(
        f"  {f['name']}: {f['impact']:+.4f}"
        for f in shap_result["top_features"][:7]
    )
    metrics_str = "\n".join(
        f"  {k}: {v}" for k, v in (metrics or {}).items()
    )
    prompt = _PROMPT.format(
        features=features_str,
        weights=weights,
        profile_desc=profile_desc or "Non spécifié",
        metrics=metrics_str or "N/A",
    )

    try:
        resp = httpx.post(
            settings.OPENROUTER_BASE_URL,
            headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
            json={
                "model": settings.LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": settings.LLM_MAX_TOKENS,
            },
            timeout=30,
        )
        resp.raise_for_status()
        msg = resp.json()["choices"][0]["message"]
        text = msg.get("content") or msg.get("reasoning") or ""
        return text.strip() if text.strip() else _fallback(shap_result, profile_desc)
    except Exception as exc:
        logger.warning("LLM call failed: %s", exc)
        return _fallback(shap_result, profile_desc)


def _fallback(shap_result: dict, profile_desc: str = "") -> str:
    top = shap_result["top_features"][:3]
    parts = [f"{f['name']} (impact {f['impact']:+.4f})" for f in top]
    base = f"Facteurs déterminants : {', '.join(parts)}."
    if profile_desc:
        base = f"{profile_desc}\n{base}"
    return base
