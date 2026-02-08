"""
Modular scraper engine for Tunisian financial news sources.

Each source has its own parser function.  If one source fails the others
continue — errors are logged and returned so the caller can report them.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Callable, List
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.config import SCRAPER_SOURCES

logger = logging.getLogger(__name__)

# ── Data container for a raw scraped article ────────────
@dataclass
class RawArticle:
    source: str
    title: str
    url: str | None = None
    content_snippet: str | None = None
    language: str = "fr"


# ── HTTP helper ─────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,ar;q=0.8,en;q=0.7",
}


async def _fetch_html(url: str, timeout: float = 15.0) -> str:
    """Return the decoded HTML body of *url*."""
    async with httpx.AsyncClient(
        headers=_HEADERS,
        follow_redirects=True,
        timeout=timeout,
        verify=False,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


# Navigation / junk patterns to filter out
_NAV_WORDS = {
    "connexion", "login", "inscription", "register", "accueil", "home",
    "contact", "recherche", "search", "menu", "mon espace", "mon profil",
    "français", "english", "عربي", "annuaires", "espace annonceurs",
    "dossiers", "immo-neuf", "taux de change", "annonces", "publicité",
    "confidentialité", "conditions", "plan du site", "a propos",
    "nous contacter", "contactez-nous", "copyright", "voir plus",
    "lire la suite", "plus d'articles", "rss", "newsletter",
    "s'abonner", "je m'abonne", "se connecter",
}

# Minimum title length to be a real article
_MIN_TITLE_LEN = 20


def _is_nav_junk(title: str, href: str | None = None) -> bool:
    """Return True if the title looks like a navigation element, not an article."""
    t = title.lower().strip()
    # Too short
    if len(t) < _MIN_TITLE_LEN:
        return True
    # Exact nav match
    if t in _NAV_WORDS:
        return True
    # Starts with a nav word
    for nw in _NAV_WORDS:
        if t == nw:
            return True
    # URL-based checks
    if href:
        path = urlparse(href).path.rstrip("/")
        # Very short paths are usually nav (e.g. /login, /account, /)
        segments = [s for s in path.split("/") if s]
        if len(segments) <= 1 and len(t) < 30:
            return True
    return False


# ── Per-source parsers ──────────────────────────────────


def _parse_ilboursa(html: str) -> List[RawArticle]:
    """
    Parse IlBoursa financial news listing page.
    Articles are <a> links pointing to /marches/... or /economie/... URLs
    with real headlines.
    """
    soup = BeautifulSoup(html, "lxml")
    articles: list[RawArticle] = []
    seen: set[str] = set()

    # IlBoursa article patterns in href
    article_patterns = re.compile(
        r"/(marches|economie|bourse|startup|analyses)/", re.IGNORECASE
    )

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"] or ""
        if not article_patterns.search(href):
            continue

        title = a_tag.get_text(strip=True)
        if not title or title in seen or _is_nav_junk(title, href):
            continue
        seen.add(title)

        if not href.startswith("http"):
            href = "https://www.ilboursa.com" + href

        articles.append(
            RawArticle(
                source="IlBoursa",
                title=title,
                url=href,
                content_snippet=title,
                language="fr",
            )
        )

    return articles[:25]


def _parse_tustex(html: str) -> List[RawArticle]:
    """
    Parse Tustex stock-news page.
    Articles are <a> links with long hrefs containing bourse-*, economie-*, etc.
    """
    soup = BeautifulSoup(html, "lxml")
    articles: list[RawArticle] = []
    seen: set[str] = set()

    # Tustex article URL patterns
    article_patterns = re.compile(
        r"tustex\.com/(bourse-|economie|finance|politique|maghreb|international|tustex-plus)",
        re.IGNORECASE,
    )

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"] or ""
        if not article_patterns.search(href):
            continue

        title = a_tag.get_text(strip=True)
        if not title or title in seen or _is_nav_junk(title, href):
            continue

        # Skip category-only links (e.g. /bourse-tunis, /economie/emploi)
        path = urlparse(href).path.rstrip("/")
        segments = [s for s in path.split("/") if s]
        if len(segments) < 2:
            continue

        seen.add(title)

        if not href.startswith("http"):
            href = "https://www.tustex.com" + href

        articles.append(
            RawArticle(
                source="Tustex",
                title=title,
                url=href,
                content_snippet=title,
                language="fr",
            )
        )

    return articles[:25]


def _parse_tunisie_numerique(html: str) -> List[RawArticle]:
    """
    Parse TunisieNumerique economy section.
    Articles are <a> links with long slugified URLs pointing to real articles.
    """
    soup = BeautifulSoup(html, "lxml")
    articles: list[RawArticle] = []
    seen: set[str] = set()

    # TunisieNumerique article URLs have long slugs
    # Nav links are short (/login, /account, /category/...)
    skip_paths = re.compile(
        r"/(login|account|contact|category/|tag/|page/|liste-|espace-|feed|wp-)",
        re.IGNORECASE,
    )

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"] or ""
        if "tunisienumerique.com" not in href:
            continue
        if skip_paths.search(href):
            continue

        # Only consider links with long slugs (actual articles)
        path = urlparse(href).path.rstrip("/")
        segments = [s for s in path.split("/") if s]
        # Real articles have a slug like /la-tunisie-porte-dentree-...
        # Nav items have short paths like /actualite-tunisie/economie
        last_segment = segments[-1] if segments else ""
        if len(last_segment) < 15:
            continue

        title = a_tag.get_text(strip=True)
        if not title or title in seen or _is_nav_junk(title, href):
            continue
        seen.add(title)

        # Try to detect language from title (Arabic chars present?)
        has_arabic = bool(re.search(r"[\u0600-\u06FF]", title))
        lang = "ar" if has_arabic else "fr"

        articles.append(
            RawArticle(
                source="TunisieNumerique",
                title=title,
                url=href,
                content_snippet=title,
                language=lang,
            )
        )

    return articles[:25]


# ── Source → parser mapping ─────────────────────────────

_PARSERS: dict[str, Callable[[str], List[RawArticle]]] = {
    "IlBoursa": _parse_ilboursa,
    "Tustex": _parse_tustex,
    "TunisieNumerique": _parse_tunisie_numerique,
}


# ── Public entry point ──────────────────────────────────

@dataclass
class ScrapeResult:
    articles: List[RawArticle] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


async def scrape_all_sources() -> ScrapeResult:
    """
    Scrape every configured source.  Each source is independent — if one
    fails the others still run.
    """
    result = ScrapeResult()

    for source_cfg in SCRAPER_SOURCES:
        name = source_cfg["name"]
        url = source_cfg["url"]
        parser = _PARSERS.get(name)

        if parser is None:
            result.errors.append(f"No parser registered for source '{name}'")
            continue

        try:
            logger.info("Scraping %s → %s", name, url)
            html = await _fetch_html(url)
            articles = parser(html)
            logger.info("  ✓ %d articles from %s", len(articles), name)
            result.articles.extend(articles)
        except httpx.HTTPStatusError as exc:
            msg = f"[{name}] HTTP {exc.response.status_code} from {url}"
            logger.warning(msg)
            result.errors.append(msg)
        except httpx.RequestError as exc:
            msg = f"[{name}] Request error: {exc}"
            logger.warning(msg)
            result.errors.append(msg)
        except Exception as exc:
            msg = f"[{name}] Unexpected error: {exc}"
            logger.exception(msg)
            result.errors.append(msg)

    return result
