"""Agent Prospection — détecte, enrichit, score et prépare l'approche.

Le module complète `routes/growth.py` au lieu de le remplacer : les leads sont
écrits dans la MÊME table `user_leads`, avec la même forme d'enregistrement, et
apparaissent donc directement dans le pipeline Croissance existant.

Cycle complet d'un scan
───────────────────────
  1. COLLECTE   trois familles de sources, activables indépendamment :
                • entreprises   → API Recherche d'entreprises (data.gouv, sans
                                  clé) et/ou API Sirene INSEE si une clé existe
                • commerces     → Google Places Text Search (clé requise)
                • intentions    → Reddit + HackerNews (déjà présents dans growth)
  2. DÉDOUBLONNAGE  par SIRET, par place_id, par URL, puis par nom normalisé.
  3. ENRICHISSEMENT le site web du prospect est lu puis résumé en JSON structuré
                    par le LLM (voir `_extraire_fiche`). C'est la brique de type
                    « scraping piloté par IA ».
  4. SCORING    correspondance avec le profil de client idéal (ICP), 0 à 100,
                calculée à partir de faits vérifiables — jamais d'un ressenti.
  5. APPROCHE   un brouillon personnalisé est rédigé À LA DEMANDE et n'est
                JAMAIS envoyé automatiquement (voir la note « Consentement »).

Note technique — pourquoi pas la bibliothèque ScrapeGraphAI directement
──────────────────────────────────────────────────────────────────────
ScrapeGraphAI fait exactement ce que fait `_enrichir_prospect` : récupérer une
page, la nettoyer, la donner à un LLM avec un schéma de sortie. Mais elle tire
langchain, un navigateur headless et leurs dépendances — plusieurs centaines de
Mo dans l'image Docker Railway, pour un service qui tourne déjà avec httpx,
BeautifulSoup et un client LLM. On implémente donc le même motif nativement,
avec le fournisseur IA déjà payé par Zayado (Mammouth).

L'API hébergée de ScrapeGraphAI reste branchable sans toucher au reste : posez
SCRAPEGRAPH_API_KEY et `_extraire_fiche` l'utilisera à la place du chemin natif.
Utile pour les sites lourds en JavaScript, que httpx seul ne peut pas rendre.

Note juridique — collecte et prospection B2B
────────────────────────────────────────────
Chaque lead conserve sa source exacte, l'horodatage de collecte et sa base
légale. Trois règles appliquées dans le code, pas seulement dans la doc :
  • robots.txt est lu et respecté avant toute lecture de page (`_robots_autorise`)
  • les adresses nominatives (prenom.nom@) sont marquées `email_nominatif`, ce
    qui déclenche l'obligation d'information de l'article 14 du RGPD ; le texte
    est généré par `GET /prospection/mention-information`
  • aucun envoi automatique : l'agent rédige, l'utilisateur relit et décide
"""
import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User

from routes.growth import (
    _get_kv, _save_kv, _list_leads, _save_lead,
    _fetch_sirene_companies, _fetch_reddit, _fetch_hackernews,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/prospection", tags=["prospection"])

# ─────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────
RECHERCHE_ENTREPRISES_URL = "https://recherche-entreprises.api.gouv.fr/search"
GOOGLE_PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
SCRAPEGRAPH_API_KEY = os.environ.get("SCRAPEGRAPH_API_KEY", "")
SCRAPEGRAPH_URL = os.environ.get("SCRAPEGRAPH_URL", "https://api.scrapegraphai.com/v1/smartscraper")

# Un agent qui lit des sites doit se présenter. Une adresse de contact dans le
# user-agent permet à un webmaster de nous joindre plutôt que de nous bloquer.
USER_AGENT = os.environ.get(
    "PROSPECTION_USER_AGENT",
    "ZayadoProspectionBot/1.0 (+https://zayado.net/robots; contact@zayado.net)",
)
PAGE_MAX_OCTETS = 900_000      # au-delà, la page n'apporte plus rien d'utile
PAGE_MAX_CARACTERES = 12_000   # ce qu'on transmet au LLM après nettoyage
DELAI_ENTRE_SITES = 1.0        # seconde — on ne martèle pas les serveurs tiers
MAX_ENRICHISSEMENTS_PAR_SCAN = 12

CLE_ICP = "prospection_icp"
CLE_HISTORIQUE = "prospection_runs"

ICP_DEFAUT = {
    "offre": "",              # ce que l'utilisateur vend, en une phrase
    "probleme_resolu": "",    # le problème que ça règle chez le client
    "secteur": "",            # secteur visé, en clair
    "code_naf": "",           # optionnel, affine la source entreprises
    "departement": "",        # ex "44" ou "44000"
    "ville": "",              # pour les commerces locaux
    "type_commerce": "",      # ex "boulangerie", "cabinet comptable"
    "taille_visee": "tpe",    # tpe | pme | indifferent
    "mots_cles_intention": [],
    "subreddits": [],
    "signaux_positifs": [],   # ex ["recrute", "vient d'ouvrir", "site vieillissant"]
    "signaux_redhibitoires": [],
    "ton": "direct",          # direct | chaleureux | expert
    "langue": "fr",
}

SOURCES = ["entreprises", "commerces", "intentions"]


def _maintenant() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────
# Lecture de pages web — robots.txt, plafonds, nettoyage
# ─────────────────────────────────────────────────────────────────
_cache_robots: dict[str, Optional[RobotFileParser]] = {}


async def _robots_autorise(url: str) -> bool:
    """Vrai si robots.txt du domaine autorise notre agent à lire `url`.

    Un robots.txt absent, vide ou illisible vaut autorisation — c'est la
    convention du web. Un robots.txt qui nous interdit est respecté : c'est la
    différence entre un agent correct et un aspirateur.
    """
    try:
        parts = urlparse(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            return False
        racine = f"{parts.scheme}://{parts.netloc}"
        if racine not in _cache_robots:
            parser: Optional[RobotFileParser] = None
            try:
                async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                    r = await client.get(f"{racine}/robots.txt", headers={"User-Agent": USER_AGENT})
                if r.status_code == 200 and r.text.strip():
                    parser = RobotFileParser()
                    parser.parse(r.text.splitlines())
            except Exception:
                parser = None
            _cache_robots[racine] = parser
        parser = _cache_robots[racine]
        if parser is None:
            return True
        return parser.can_fetch(USER_AGENT, url)
    except Exception:
        return True


async def _lire_page(url: str) -> Optional[str]:
    """Récupère le texte visible d'une page, ou None si inaccessible.

    Best-effort assumé : un site lent, protégé ou en JavaScript pur ne doit
    jamais faire échouer un scan. Le prospect est alors conservé sans fiche
    enrichie plutôt que perdu.
    """
    if not await _robots_autorise(url):
        logger.info("prospection: robots.txt interdit %s", url)
        return None
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "fr,en;q=0.8"})
            if r.status_code >= 400:
                return None
            contenu = (r.headers.get("content-type") or "").lower()
            if "html" not in contenu and "text" not in contenu:
                return None
            brut = r.text[:PAGE_MAX_OCTETS]
    except Exception as e:
        logger.info("prospection: page illisible %s (%s)", url, e)
        return None
    return _nettoyer_html(brut)


def _nettoyer_html(html: str) -> str:
    """Ne garde que le texte porteur de sens.

    Les menus, scripts et pieds de page occupent l'essentiel du volume d'une
    page vitrine et n'apprennent rien sur l'entreprise : les envoyer au LLM
    coûterait des jetons pour dégrader la qualité de l'extraction.
    """
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
    for balise in soup(["script", "style", "noscript", "svg", "iframe", "form"]):
        balise.decompose()
    texte = soup.get_text(separator="\n")
    lignes = [l.strip() for l in texte.splitlines()]
    lignes = [l for l in lignes if len(l) > 1]
    return "\n".join(lignes)[:PAGE_MAX_CARACTERES]


_RE_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_RE_TEL_FR = re.compile(r"(?:(?:\+33|0033)\s?[1-9]|0[1-9])(?:[\s.\-]?\d{2}){4}")
_EMAILS_A_IGNORER = ("example.", "sentry.", "wixpress.", "@2x", ".png", ".jpg", ".webp")


def _emails_dans(texte: str) -> list[str]:
    trouves = []
    for e in _RE_EMAIL.findall(texte or ""):
        bas = e.lower()
        if any(motif in bas for motif in _EMAILS_A_IGNORER):
            continue
        if bas not in trouves:
            trouves.append(bas)
    return trouves[:5]


def _est_nominatif(email: str) -> bool:
    """Une adresse nominative identifie une personne : le RGPD s'applique
    pleinement. Une adresse générique (contact@, info@) vise la structure."""
    local = (email or "").split("@")[0].lower()
    generiques = {
        "contact", "info", "infos", "bonjour", "hello", "accueil", "commercial",
        "commande", "commandes", "service", "sav", "support", "secretariat",
        "direction", "admin", "administration", "compta", "comptabilite",
        "rh", "recrutement", "presse", "devis", "reservation", "boutique",
        "no-reply", "noreply", "ne-pas-repondre",
    }
    if local in generiques:
        return False
    return bool(re.search(r"[._\-]", local)) or len(local) > 2


# ─────────────────────────────────────────────────────────────────
# Extraction structurée — le cœur « scraping piloté par IA »
# ─────────────────────────────────────────────────────────────────
SCHEMA_FICHE = {
    "activite": "ce que fait l'entreprise, une phrase factuelle",
    "proposition": "sa promesse commerciale telle qu'elle l'écrit, ou null",
    "cible": "à qui elle s'adresse, ou null",
    "taille_indices": "indices de taille (équipe, agences, effectif), ou null",
    "email": "email de contact trouvé sur la page, ou null",
    "telephone": "téléphone trouvé, ou null",
    "ville": "ville d'implantation, ou null",
    "signaux": "liste de faits notables (recrutement, ouverture, refonte, e-commerce absent…)",
    "maturite_web": "faible | correcte | forte",
}

INSTRUCTION_EXTRACTION = (
    "Tu extrais des faits d'une page web d'entreprise. Réponds UNIQUEMENT par un objet "
    "JSON valide, sans texte autour, sans bloc de code.\n"
    "Règle absolue : n'invente RIEN. Si une information n'apparaît pas dans la page, "
    "mets null. Une hypothèse plausible est une erreur, pas une aide.\n"
    "Le champ 'signaux' est une liste de courtes chaînes, faits observés uniquement.\n"
    f"Clés attendues et contenu : {json.dumps(SCHEMA_FICHE, ensure_ascii=False)}"
)


def _json_depuis_llm(reponse: str) -> dict:
    """Récupère l'objet JSON d'une réponse de LLM.

    Même avec une consigne stricte, un modèle encadre parfois sa réponse d'un
    bloc ``` ou d'une phrase d'introduction. Plutôt que de perdre l'extraction,
    on isole le premier objet équilibré.
    """
    if not reponse:
        return {}
    texte = reponse.strip()
    texte = re.sub(r"^```(?:json)?\s*", "", texte)
    texte = re.sub(r"\s*```$", "", texte)
    try:
        valeur = json.loads(texte)
        return valeur if isinstance(valeur, dict) else {}
    except Exception:
        pass
    debut = texte.find("{")
    if debut == -1:
        return {}
    profondeur = 0
    for i in range(debut, len(texte)):
        if texte[i] == "{":
            profondeur += 1
        elif texte[i] == "}":
            profondeur -= 1
            if profondeur == 0:
                try:
                    valeur = json.loads(texte[debut:i + 1])
                    return valeur if isinstance(valeur, dict) else {}
                except Exception:
                    return {}
    return {}


async def _extraire_fiche(url: str, texte: str) -> dict:
    """Transforme le texte d'une page en fiche structurée.

    Deux moteurs interchangeables : l'API hébergée ScrapeGraphAI si une clé est
    posée (meilleure sur les sites rendus en JavaScript), sinon le LLM déjà
    utilisé par Zayado. Le contrat de sortie est identique dans les deux cas.
    """
    if SCRAPEGRAPH_API_KEY:
        fiche = await _extraire_via_scrapegraph(url)
        if fiche:
            return fiche
    if not texte:
        return {}
    try:
        from mammouth_client import chat as ai_chat
        reponse = await ai_chat(
            [
                {"role": "system", "content": INSTRUCTION_EXTRACTION},
                {"role": "user", "content": f"URL : {url}\n\nContenu de la page :\n{texte}"},
            ],
            max_tokens=700,
            temperature=0.0,  # extraction de faits : aucune créativité souhaitée
        )
        return _json_depuis_llm(reponse)
    except Exception as e:
        logger.warning("prospection: extraction IA impossible pour %s (%s)", url, e)
        return {}


async def _extraire_via_scrapegraph(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            r = await client.post(
                SCRAPEGRAPH_URL,
                headers={"SGAI-APIKEY": SCRAPEGRAPH_API_KEY, "Content-Type": "application/json"},
                json={
                    "website_url": url,
                    "user_prompt": INSTRUCTION_EXTRACTION,
                },
            )
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.warning("prospection: ScrapeGraphAI indisponible (%s) — repli natif", e)
        return {}
    resultat = data.get("result") if isinstance(data, dict) else None
    if isinstance(resultat, dict):
        return resultat
    if isinstance(resultat, str):
        return _json_depuis_llm(resultat)
    return {}


# ─────────────────────────────────────────────────────────────────
# Sources
# ─────────────────────────────────────────────────────────────────
async def _source_entreprises(icp: dict, limite: int) -> list[dict]:
    """Entreprises françaises. API Recherche d'entreprises en premier : ouverte,
    sans clé, elle rend l'agent utilisable immédiatement. L'API Sirene INSEE,
    plus riche, s'ajoute quand la clé est configurée."""
    candidats: list[dict] = []
    params = {"per_page": str(min(limite, 25)), "page": "1"}
    terme = (icp.get("secteur") or icp.get("type_commerce") or "").strip()
    if terme:
        params["q"] = terme
    if icp.get("code_naf"):
        params["activite_principale"] = icp["code_naf"]
    if icp.get("departement"):
        params["departement"] = icp["departement"][:2]
    if icp.get("taille_visee") == "tpe":
        params["tranche_effectif_salarie"] = "00,01,02,03"
    if "q" not in params and "activite_principale" not in params:
        return []  # une recherche sans critère ramènerait n'importe quoi

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(RECHERCHE_ENTREPRISES_URL, params=params,
                                 headers={"User-Agent": USER_AGENT})
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.warning("prospection: Recherche d'entreprises indisponible (%s)", e)
        data = {}

    for item in (data.get("results") or []):
        siege = item.get("siege") or {}
        candidats.append({
            "cle": siege.get("siret") or item.get("siren") or item.get("nom_complet"),
            "nom": item.get("nom_complet") or item.get("nom_raison_sociale") or "Entreprise",
            "siret": siege.get("siret") or "",
            "ville": siege.get("libelle_commune") or "",
            "naf": item.get("activite_principale") or "",
            "date_creation": item.get("date_creation") or "",
            "effectif": item.get("tranche_effectif_salarie") or "",
            "site": (siege.get("site_internet") or item.get("site_internet") or "").strip(),
            "source": "recherche-entreprises",
            "source_url": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{item.get('siren', '')}",
        })

    if len(candidats) < limite and icp.get("code_naf"):
        try:
            insee = await _fetch_sirene_companies(icp["code_naf"], icp.get("departement", ""),
                                                  limit=limite - len(candidats))
            for c in insee:
                candidats.append({
                    "cle": c.get("siret"),
                    "nom": c.get("name") or "Entreprise",
                    "siret": c.get("siret") or "",
                    "ville": c.get("ville") or "",
                    "naf": c.get("naf") or "",
                    "date_creation": c.get("date_creation") or "",
                    "effectif": "",
                    "site": "",
                    "source": "sirene",
                    "source_url": "https://api.insee.fr/entreprises/sirene",
                })
        except Exception as e:
            logger.info("prospection: source Sirene ignorée (%s)", e)
    return candidats[:limite]


async def _source_commerces(icp: dict, limite: int) -> list[dict]:
    """Commerces et professionnels locaux via Google Places."""
    if not GOOGLE_PLACES_API_KEY:
        return []
    quoi = (icp.get("type_commerce") or icp.get("secteur") or "").strip()
    ou = (icp.get("ville") or icp.get("departement") or "").strip()
    if not quoi or not ou:
        return []
    champs = ("places.id,places.displayName,places.formattedAddress,places.websiteUri,"
              "places.nationalPhoneNumber,places.rating,places.userRatingCount,places.primaryTypeDisplayName")
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.post(
                GOOGLE_PLACES_URL,
                headers={
                    "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
                    "X-Goog-FieldMask": champs,
                    "Content-Type": "application/json",
                },
                json={"textQuery": f"{quoi} {ou}", "languageCode": "fr",
                      "maxResultCount": min(limite, 20)},
            )
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.warning("prospection: Google Places indisponible (%s)", e)
        return []

    sortie = []
    for p in (data.get("places") or [])[:limite]:
        nom = (p.get("displayName") or {}).get("text") or "Commerce"
        sortie.append({
            "cle": p.get("id") or nom,
            "nom": nom,
            "siret": "",
            "ville": p.get("formattedAddress") or ou,
            "naf": (p.get("primaryTypeDisplayName") or {}).get("text") or quoi,
            "date_creation": "",
            "effectif": "",
            "site": (p.get("websiteUri") or "").strip(),
            "telephone": p.get("nationalPhoneNumber") or "",
            "note": p.get("rating"),
            "avis": p.get("userRatingCount"),
            "source": "google-places",
            "source_url": p.get("websiteUri") or "",
        })
    return sortie


async def _source_intentions(icp: dict, limite: int) -> list[dict]:
    """Personnes qui expriment publiquement un besoin.

    Ce n'est pas la même matière que les deux autres sources : il n'y a pas
    d'entreprise à enrichir, mais un message daté et son auteur. On le conserve
    tel quel, avec son lien, pour que l'utilisateur juge sur pièce.
    """
    mots = [m for m in (icp.get("mots_cles_intention") or []) if m]
    if not mots:
        return []
    requete = " ".join(mots[:5])
    subreddits = icp.get("subreddits") or []
    resultats: list[dict] = []
    try:
        resultats += await _fetch_reddit(requete, subreddits, limite)
    except Exception as e:
        logger.info("prospection: Reddit indisponible (%s)", e)
    try:
        resultats += await _fetch_hackernews(requete, limite)
    except Exception as e:
        logger.info("prospection: HackerNews indisponible (%s)", e)

    # Forme renvoyée par growth._fetch_reddit / _fetch_hackernews :
    # {id, author, subreddit, title, selftext, permalink, created}
    sortie = []
    for item in resultats[:limite]:
        titre = (item.get("title") or "").strip() or "Besoin exprimé"
        cree = item.get("created")
        try:
            date_iso = datetime.fromtimestamp(float(cree), tz=timezone.utc).isoformat() if cree else ""
        except Exception:
            date_iso = ""
        espace = item.get("subreddit") or ""
        sortie.append({
            "cle": item.get("permalink") or item.get("id") or titre,
            "nom": titre[:120],
            "siret": "",
            "ville": "",
            "naf": "",
            "date_creation": date_iso,
            "effectif": "",
            "site": "",
            "extrait": (item.get("selftext") or "")[:400],
            "auteur": item.get("author") or "",
            "source": "hackernews" if espace == "HackerNews" else "reddit",
            "source_url": item.get("permalink") or "",
        })
    return sortie


# ─────────────────────────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────────────────────────
def _score_prospect(candidat: dict, fiche: dict, icp: dict) -> tuple[int, list[str]]:
    """Score de correspondance 0–100, avec la liste des raisons.

    Le score est délibérément explicable : chaque point vient d'un fait
    vérifiable, et l'utilisateur voit pourquoi. Un score opaque produit soit
    une confiance excessive, soit un rejet en bloc — jamais un bon arbitrage.
    """
    score = 40  # un prospect issu d'une source ciblée part d'un socle neutre
    raisons: list[str] = []

    joignable = fiche.get("email") or candidat.get("email") or candidat.get("telephone") or fiche.get("telephone")
    if joignable:
        score += 15
        raisons.append("Coordonnées de contact trouvées")
    else:
        score -= 10
        raisons.append("Aucune coordonnée directe — approche plus difficile")

    if candidat.get("site"):
        score += 5
        raisons.append("Présence web identifiée")
    elif candidat.get("source") in ("recherche-entreprises", "sirene", "google-places"):
        score -= 5
        raisons.append("Pas de site web connu")

    activite = " ".join(filter(None, [
        str(fiche.get("activite") or ""), str(fiche.get("proposition") or ""),
        str(candidat.get("naf") or ""), str(candidat.get("extrait") or ""),
    ])).lower()

    secteur = (icp.get("secteur") or "").lower().strip()
    if secteur and any(mot in activite for mot in secteur.split() if len(mot) > 3):
        score += 12
        raisons.append(f"Activité cohérente avec « {icp['secteur']} »")

    signaux_fiche = fiche.get("signaux")
    signaux_texte = " ".join(signaux_fiche).lower() if isinstance(signaux_fiche, list) else str(signaux_fiche or "").lower()
    for signal in (icp.get("signaux_positifs") or []):
        if signal and signal.lower() in (signaux_texte + " " + activite):
            score += 8
            raisons.append(f"Signal recherché présent : {signal}")
    for signal in (icp.get("signaux_redhibitoires") or []):
        if signal and signal.lower() in (signaux_texte + " " + activite):
            score -= 30
            raisons.append(f"Signal rédhibitoire : {signal}")

    if fiche.get("maturite_web") == "faible":
        score += 6
        raisons.append("Maturité web faible — marge de progression visible")

    # Une entreprise créée dans l'année a des besoins encore ouverts.
    creation = str(candidat.get("date_creation") or "")[:4]
    if creation.isdigit() and int(creation) >= datetime.now(timezone.utc).year - 1:
        score += 8
        raisons.append("Structure récente")

    avis = candidat.get("avis")
    if isinstance(avis, int) and avis < 10 and candidat.get("source") == "google-places":
        score += 5
        raisons.append("Peu d'avis en ligne — visibilité à construire")

    if candidat.get("source") in ("reddit", "hackernews", "intention"):
        score += 10
        raisons.append("Besoin exprimé publiquement")

    return max(0, min(100, score)), raisons


# ─────────────────────────────────────────────────────────────────
# Enrichissement d'un candidat
# ─────────────────────────────────────────────────────────────────
async def _enrichir_prospect(candidat: dict) -> dict:
    site = (candidat.get("site") or "").strip()
    if not site:
        return {}
    if not site.startswith("http"):
        site = "https://" + site.lstrip("/")
    texte = await _lire_page(site)
    fiche = await _extraire_fiche(site, texte or "")

    # Filet : si le LLM n'a pas vu l'email, une expression régulière le trouve
    # souvent quand même. On préfère un fait brut à une case vide.
    if texte:
        if not fiche.get("email"):
            emails = _emails_dans(texte)
            if emails:
                fiche["email"] = emails[0]
        if not fiche.get("telephone"):
            tel = _RE_TEL_FR.search(texte)
            if tel:
                fiche["telephone"] = tel.group(0)
    if fiche:
        fiche["_url_lue"] = site
        fiche["_lu_le"] = _maintenant()
    return fiche


def _lead_depuis(candidat: dict, fiche: dict, score: int, raisons: list[str], icp: dict) -> dict:
    email = fiche.get("email") or candidat.get("email") or ""
    ville = fiche.get("ville") or candidat.get("ville") or ""
    activite = fiche.get("activite") or candidat.get("naf") or ""
    extrait = candidat.get("extrait") or ""

    morceaux = [m for m in [activite, ville] if m]
    if candidat.get("siret"):
        morceaux.append(f"SIRET {candidat['siret']}")
    if extrait:
        morceaux.append(extrait[:180])

    return {
        "id": str(uuid.uuid4()),
        "name": candidat.get("nom") or "Prospect",
        "company": candidat.get("nom") or "",
        "email": email,
        "siret": candidat.get("siret") or "",
        "sub": ville or candidat.get("auteur") or "",
        "snippet": " · ".join(morceaux)[:400],
        "source": candidat.get("source") or "prospection",
        "stage": "detected",
        "campaign": "agent-prospection",
        "date": candidat.get("date_creation") or "",
        # ── Champs propres à l'agent ────────────────────────────
        "score": score,
        "score_raisons": raisons,
        "fiche": fiche,
        "site": candidat.get("site") or fiche.get("_url_lue") or "",
        "telephone": fiche.get("telephone") or candidat.get("telephone") or "",
        # ── Traçabilité et conformité ───────────────────────────
        "source_url": candidat.get("source_url") or "",
        "collecte_le": _maintenant(),
        "base_legale": "interet_legitime_prospection_b2b",
        "email_nominatif": bool(email) and _est_nominatif(email),
        "information_envoyee": False,
        "icp_utilise": {"secteur": icp.get("secteur"), "offre": icp.get("offre")},
    }


# ─────────────────────────────────────────────────────────────────
# Endpoints — profil de client idéal
# ─────────────────────────────────────────────────────────────────
@router.get("/icp")
async def lire_icp(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    enregistre = await _get_kv(db, user.id, CLE_ICP) or {}
    return {**ICP_DEFAUT, **enregistre}


@router.put("/icp")
async def ecrire_icp(patch: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    actuel = await _get_kv(db, user.id, CLE_ICP) or {}
    fusion = {**ICP_DEFAUT, **actuel, **(patch or {})}
    for cle in ("mots_cles_intention", "subreddits", "signaux_positifs", "signaux_redhibitoires"):
        valeur = fusion.get(cle)
        if isinstance(valeur, str):
            fusion[cle] = [v.strip() for v in valeur.split(",") if v.strip()]
        elif not isinstance(valeur, list):
            fusion[cle] = []
    await _save_kv(db, user.id, CLE_ICP, fusion)
    return fusion


@router.get("/sources")
async def etat_sources(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Dit franchement ce qui est utilisable et ce qui manque.

    Une source non configurée doit se voir avant le scan, pas se deviner
    devant un résultat vide.
    """
    icp = {**ICP_DEFAUT, **(await _get_kv(db, user.id, CLE_ICP) or {})}
    manque_entreprises = not (icp.get("secteur") or icp.get("code_naf") or icp.get("type_commerce"))
    return {
        "sources": [
            {
                "id": "entreprises",
                "label": "Entreprises françaises",
                "detail": "Registre officiel : Recherche d'entreprises (data.gouv), complété par l'API Sirene si une clé INSEE est configurée.",
                "pret": not manque_entreprises,
                "manque": "Renseignez un secteur ou un code NAF dans votre profil client idéal." if manque_entreprises else "",
                "cle_requise": False,
            },
            {
                "id": "commerces",
                "label": "Commerces et pros locaux",
                "detail": "Google Places : nom, adresse, site, téléphone, avis.",
                "pret": bool(GOOGLE_PLACES_API_KEY) and bool(icp.get("ville") and (icp.get("type_commerce") or icp.get("secteur"))),
                "manque": ("Variable d'environnement GOOGLE_PLACES_API_KEY absente côté serveur."
                           if not GOOGLE_PLACES_API_KEY
                           else "Renseignez une ville et un type de commerce." if not (icp.get("ville") and (icp.get("type_commerce") or icp.get("secteur"))) else ""),
                "cle_requise": True,
            },
            {
                "id": "intentions",
                "label": "Besoins exprimés en ligne",
                "detail": "Reddit et HackerNews : messages publics où quelqu'un cherche ce que vous vendez.",
                "pret": bool(icp.get("mots_cles_intention")),
                "manque": "Ajoutez des mots-clés d'intention (ex : « cherche comptable », « besoin d'un site »)." if not icp.get("mots_cles_intention") else "",
                "cle_requise": False,
            },
        ],
        "enrichissement": {
            "moteur": "ScrapeGraphAI (API hébergée)" if SCRAPEGRAPH_API_KEY else "Extraction IA native (Mammouth)",
            "note": "Le moteur natif ne rend pas le JavaScript. Posez SCRAPEGRAPH_API_KEY pour les sites qui en dépendent.",
        },
    }


# ─────────────────────────────────────────────────────────────────
# Endpoint — scan
# ─────────────────────────────────────────────────────────────────
class ScanIn(BaseModel):
    sources: Optional[list[str]] = None
    limite: Optional[int] = 15
    enrichir: Optional[bool] = True


@router.post("/scan")
async def scan(body: ScanIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    icp = {**ICP_DEFAUT, **(await _get_kv(db, user.id, CLE_ICP) or {})}
    demandees = [s for s in (body.sources or SOURCES) if s in SOURCES]
    if not demandees:
        raise HTTPException(400, "Aucune source valide sélectionnée.")
    limite = max(1, min(int(body.limite or 15), 30))

    # ── 1. Collecte ────────────────────────────────────────────
    collectes: list[dict] = []
    journal: list[str] = []
    for nom_source in demandees:
        try:
            if nom_source == "entreprises":
                trouves = await _source_entreprises(icp, limite)
            elif nom_source == "commerces":
                trouves = await _source_commerces(icp, limite)
            else:
                trouves = await _source_intentions(icp, limite)
        except Exception as e:
            logger.warning("prospection: source %s en échec (%s)", nom_source, e)
            journal.append(f"{nom_source} : indisponible")
            continue
        journal.append(f"{nom_source} : {len(trouves)} résultat(s)")
        collectes += trouves

    if not collectes:
        return {
            "nouveaux": 0, "examines": 0, "leads": [], "journal": journal,
            "message": "Aucun résultat. Vérifiez votre profil client idéal et l'état des sources.",
        }

    # ── 2. Dédoublonnage, y compris contre les leads déjà en base ──
    existants = await _list_leads(db, user.id)
    deja = set()
    for lead in existants:
        for champ in ("siret", "source_url", "site"):
            if lead.get(champ):
                deja.add(str(lead[champ]).lower())
        if lead.get("name"):
            deja.add(_normaliser(lead["name"]))

    retenus: list[dict] = []
    for candidat in collectes:
        empreintes = {str(candidat.get(c)).lower() for c in ("siret", "source_url", "site") if candidat.get(c)}
        empreintes.add(_normaliser(candidat.get("nom") or ""))
        if empreintes & deja:
            continue
        deja |= empreintes
        retenus.append(candidat)

    # ── 3. Enrichissement (plafonné : chaque site coûte du temps et des jetons) ──
    fiches: dict[int, dict] = {}
    if body.enrichir:
        a_enrichir = [i for i, c in enumerate(retenus) if c.get("site")][:MAX_ENRICHISSEMENTS_PAR_SCAN]
        for rang, index in enumerate(a_enrichir):
            if rang:
                await asyncio.sleep(DELAI_ENTRE_SITES)
            fiches[index] = await _enrichir_prospect(retenus[index])
        journal.append(f"enrichissement : {len(a_enrichir)} site(s) lu(s)")

    # ── 4. Scoring et enregistrement ───────────────────────────
    crees = []
    for index, candidat in enumerate(retenus):
        fiche = fiches.get(index, {})
        score, raisons = _score_prospect(candidat, fiche, icp)
        lead = _lead_depuis(candidat, fiche, score, raisons, icp)
        try:
            await _save_lead(db, user.id, lead)
            crees.append(lead)
        except Exception as e:
            logger.warning("prospection: lead non enregistré (%s)", e)

    crees.sort(key=lambda l: l.get("score", 0), reverse=True)
    await _journaliser(db, user.id, demandees, len(collectes), len(crees))
    return {
        "nouveaux": len(crees),
        "examines": len(collectes),
        "leads": crees,
        "journal": journal,
    }


def _normaliser(nom: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (nom or "").lower())[:40]


async def _journaliser(db: AsyncSession, user_id: str, sources: list[str], examines: int, crees: int):
    historique = await _get_kv(db, user_id, CLE_HISTORIQUE) or {}
    entrees = historique.get("entrees") or []
    entrees.insert(0, {
        "date": _maintenant(), "sources": sources,
        "examines": examines, "nouveaux": crees,
    })
    await _save_kv(db, user_id, CLE_HISTORIQUE, {"entrees": entrees[:30]})


@router.get("/runs")
async def historique(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    historique = await _get_kv(db, user.id, CLE_HISTORIQUE) or {}
    return {"entrees": historique.get("entrees") or []}


# ─────────────────────────────────────────────────────────────────
# Endpoint — rédaction de l'approche
# ─────────────────────────────────────────────────────────────────
class BrouillonIn(BaseModel):
    lead_id: str
    canal: Optional[str] = "email"   # email | linkedin | telephone
    consigne: Optional[str] = None


INSTRUCTION_APPROCHE = """Tu rédiges une première prise de contact commerciale B2B, en français.

Contraintes non négociables :
- Ne JAMAIS inventer un fait sur le prospect. Tu ne disposes que de la fiche fournie.
  Si elle est pauvre, écris un message court et honnête plutôt qu'un message flatteur et faux.
- Pas de superlatif creux, pas de « j'espère que vous allez bien », pas de fausse familiarité.
- Une seule idée : pourquoi CE prospect, et une proposition concrète de suite.
- Maximum 120 mots pour un email, 60 pour LinkedIn, 5 phrases pour un script téléphonique.
- Terminer un email par une question simple, pas par une demande de rendez-vous immédiate.

Réponds en JSON strict : {"objet": "...", "message": "...", "pourquoi": "en une phrase, ce qui justifie ce message"}
Pour LinkedIn ou téléphone, "objet" vaut null."""


@router.post("/brouillon")
async def brouillon(body: BrouillonIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Rédige une approche personnalisée. N'envoie rien.

    Le choix est délibéré : un message commercial part au nom de l'utilisateur
    et engage sa réputation. L'agent prépare, l'humain relit et décide.
    """
    leads = await _list_leads(db, user.id)
    lead = next((l for l in leads if l.get("id") == body.lead_id), None)
    if not lead:
        raise HTTPException(404, "Prospect introuvable.")

    icp = {**ICP_DEFAUT, **(await _get_kv(db, user.id, CLE_ICP) or {})}
    fiche = lead.get("fiche") or {}
    contexte = {
        "prospect": lead.get("name"),
        "ville": lead.get("sub"),
        "activite": fiche.get("activite") or lead.get("snippet"),
        "proposition_du_prospect": fiche.get("proposition"),
        "signaux": fiche.get("signaux"),
        "site": lead.get("site"),
        "raisons_du_score": lead.get("score_raisons"),
        "mon_offre": icp.get("offre"),
        "probleme_que_je_resous": icp.get("probleme_resolu"),
        "ton_souhaite": icp.get("ton"),
        "canal": body.canal,
    }
    consigne = f"\n\nConsigne supplémentaire de l'utilisateur : {body.consigne}" if body.consigne else ""

    try:
        from mammouth_client import chat as ai_chat
        reponse = await ai_chat(
            [
                {"role": "system", "content": INSTRUCTION_APPROCHE},
                {"role": "user", "content": json.dumps(contexte, ensure_ascii=False, indent=2) + consigne},
            ],
            max_tokens=600,
            temperature=0.6,
        )
    except Exception as e:
        logger.warning("prospection: rédaction impossible (%s)", e)
        raise HTTPException(503, "Le service de rédaction est momentanément indisponible.")

    brouillon_json = _json_depuis_llm(reponse)
    if not brouillon_json.get("message"):
        # Le modèle a répondu en texte libre : on ne perd pas son travail.
        brouillon_json = {"objet": None, "message": (reponse or "").strip(), "pourquoi": ""}

    brouillon_json["avertissement"] = (
        "Relisez avant d'envoyer. Ce message est rédigé à partir d'informations publiques "
        "collectées automatiquement : vérifiez chaque affirmation qui concerne le prospect."
    )
    if lead.get("email_nominatif"):
        brouillon_json["rappel_rgpd"] = (
            "Cette adresse identifie une personne. Joignez la mention d'information "
            "(article 14 du RGPD) et un moyen de refus dès ce premier message."
        )
    return brouillon_json


@router.get("/mention-information")
async def mention_information(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Texte d'information à joindre aux premiers messages.

    Quand des coordonnées sont collectées ailleurs qu'auprès de la personne
    elle-même, l'article 14 du RGPD impose de l'informer. Ce texte n'est pas
    un avis juridique : faites-le valider, mais partez de quelque chose.
    """
    icp = {**ICP_DEFAUT, **(await _get_kv(db, user.id, CLE_ICP) or {})}
    expediteur = (icp.get("offre") or "notre activité").strip()
    return {
        "texte": (
            "Vos coordonnées professionnelles ont été collectées depuis des sources publiques "
            "(registre des entreprises, votre site internet ou une publication en ligne) afin de vous "
            f"présenter {expediteur}. Ce traitement repose sur notre intérêt légitime à prospecter "
            "dans un cadre professionnel. Vous pouvez demander l'accès, la rectification ou l'effacement "
            "de vos données, ou vous opposer à leur traitement, en répondant simplement à ce message. "
            "Vos coordonnées seront alors supprimées et ne seront plus utilisées."
        ),
        "rappel": (
            "À joindre au premier message dès que l'adresse identifie une personne "
            "(prenom.nom@…). Une adresse générique (contact@…) reste une bonne pratique."
        ),
    }
