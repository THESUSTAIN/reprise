"""Tests du moteur de prospection.

On teste les fonctions pures — celles qui décident. Les appels réseau et LLM
sont volontairement hors périmètre : ce qui casse en silence dans un agent de
prospection, ce n'est pas l'appel HTTP (il lève), c'est le parsing tolérant et
le calcul de score qui rendent un résultat plausible mais faux.
"""
import sys
import types
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))


def _charger_module():
    """Charge routes/prospection.py sans démarrer FastAPI, la base, ni le reste
    de l'application.

    Importer `routes.prospection` normalement exécuterait `routes/__init__.py`,
    qui monte l'application entière — donc la base, les modèles et une centaine
    de dépendances. On installe à la place des doublures minimales pour les
    quatre modules dont dépend le fichier testé, puis on le charge directement
    depuis son chemin.
    """
    import importlib.util

    def _faux_module(nom: str, **attributs):
        module = types.ModuleType(nom)
        for cle, valeur in attributs.items():
            setattr(module, cle, valeur)
        sys.modules[nom] = module
        return module

    _faux_module("database", get_db=lambda: None)
    _faux_module("deps", get_current_user=lambda: None)
    _faux_module("models", User=type("User", (), {}), UserConnection=type("UserConnection", (), {}))

    async def _stub(*_a, **_k):
        return []

    paquet = _faux_module("routes")
    paquet.__path__ = []  # paquet vide : __init__.py réel jamais exécuté
    _faux_module(
        "routes.growth",
        _get_kv=_stub, _save_kv=_stub, _list_leads=_stub, _save_lead=_stub,
        _fetch_sirene_companies=_stub, _fetch_reddit=_stub, _fetch_hackernews=_stub,
    )

    chemin = RACINE / "routes" / "prospection.py"
    spec = importlib.util.spec_from_file_location("prospection_sous_test", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prospection = _charger_module()


# ─────────────────────────────────────────────────────────────────
# Parsing de la réponse du LLM
# ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("brut, attendu", [
    ('{"activite": "boulangerie"}', {"activite": "boulangerie"}),
    ('```json\n{"activite": "plomberie"}\n```', {"activite": "plomberie"}),
    ('Voici le résultat :\n{"activite": "coiffure"}\nVoilà.', {"activite": "coiffure"}),
    ('{"a": {"b": 1}}', {"a": {"b": 1}}),
])
def test_json_depuis_llm_recupere_lobjet(brut, attendu):
    assert prospection._json_depuis_llm(brut) == attendu


@pytest.mark.parametrize("brut", ["", None, "pas de json ici", "{cassé", "[1,2,3]"])
def test_json_depuis_llm_renvoie_dict_vide_plutot_que_lever(brut):
    """Un modèle qui répond mal ne doit jamais faire échouer un scan entier."""
    assert prospection._json_depuis_llm(brut) == {}


# ─────────────────────────────────────────────────────────────────
# Qualification RGPD des adresses
# ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("email", [
    "contact@boulangerie.fr", "info@cabinet.fr", "commercial@societe.com",
    "no-reply@site.fr", "sav@magasin.fr",
])
def test_adresses_generiques_non_nominatives(email):
    assert prospection._est_nominatif(email) is False


@pytest.mark.parametrize("email", [
    "marie.dupont@societe.fr", "j-durand@cabinet.fr", "sophie_martin@agence.com",
])
def test_adresses_nominatives_detectees(email):
    """Une adresse nominative déclenche l'obligation d'information article 14."""
    assert prospection._est_nominatif(email) is True


def test_emails_ignore_les_faux_positifs():
    texte = "logo@2x.png sentry@sentry.io écrivez à contact@vraie-boite.fr"
    trouves = prospection._emails_dans(texte)
    assert "contact@vraie-boite.fr" in trouves
    assert not any("sentry" in e or "2x" in e for e in trouves)


# ─────────────────────────────────────────────────────────────────
# Nettoyage HTML
# ─────────────────────────────────────────────────────────────────
def test_nettoyage_retire_scripts_et_styles():
    html = """
    <html><head><style>.a{color:red}</style><script>var x=1;</script></head>
    <body><nav>Accueil Contact</nav><h1>Boulangerie Martin</h1>
    <p>Pain au levain depuis 1998.</p></body></html>
    """
    texte = prospection._nettoyer_html(html)
    assert "Boulangerie Martin" in texte
    assert "Pain au levain" in texte
    assert "var x" not in texte
    assert "color:red" not in texte


def test_nettoyage_plafonne_la_taille():
    """Le plafond protège le budget de jetons autant que la qualité."""
    html = "<body>" + ("mot " * 100_000) + "</body>"
    assert len(prospection._nettoyer_html(html)) <= prospection.PAGE_MAX_CARACTERES


# ─────────────────────────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────────────────────────
ICP_TEST = {
    "secteur": "boulangerie artisanale",
    "signaux_positifs": ["recrute"],
    "signaux_redhibitoires": ["fermé définitivement"],
}


def test_score_reste_dans_les_bornes():
    for candidat, fiche in [
        ({}, {}),
        ({"site": "https://a.fr", "date_creation": "2026-01-01", "avis": 2, "source": "google-places"},
         {"email": "contact@a.fr", "activite": "boulangerie artisanale", "signaux": ["recrute"], "maturite_web": "faible"}),
        ({"source": "recherche-entreprises"}, {"signaux": ["fermé définitivement"]}),
    ]:
        score, _ = prospection._score_prospect(candidat, fiche, ICP_TEST)
        assert 0 <= score <= 100


def test_prospect_joignable_score_plus_haut_que_injoignable():
    joignable, _ = prospection._score_prospect(
        {"site": "https://a.fr"}, {"email": "contact@a.fr"}, ICP_TEST)
    injoignable, _ = prospection._score_prospect({}, {}, ICP_TEST)
    assert joignable > injoignable


def test_signal_redhibitoire_fait_chuter_le_score():
    avec, _ = prospection._score_prospect(
        {"site": "https://a.fr"}, {"email": "contact@a.fr", "signaux": ["fermé définitivement"]}, ICP_TEST)
    sans, _ = prospection._score_prospect(
        {"site": "https://a.fr"}, {"email": "contact@a.fr", "signaux": []}, ICP_TEST)
    assert avec < sans - 20


def test_chaque_point_est_justifie():
    """Un score sans explication ne permet aucun arbitrage : on vérifie que la
    liste de raisons n'est jamais vide."""
    _, raisons = prospection._score_prospect({"site": "https://a.fr"}, {"email": "c@a.fr"}, ICP_TEST)
    assert raisons and all(isinstance(r, str) and r for r in raisons)


def test_signaux_acceptes_en_liste_ou_en_chaine():
    """Le LLM renvoie parfois une chaîne là où le schéma demande une liste."""
    en_liste, _ = prospection._score_prospect({}, {"signaux": ["recrute"]}, ICP_TEST)
    en_chaine, _ = prospection._score_prospect({}, {"signaux": "recrute activement"}, ICP_TEST)
    assert en_liste == en_chaine


# ─────────────────────────────────────────────────────────────────
# Dédoublonnage
# ─────────────────────────────────────────────────────────────────
def test_normalisation_rapproche_les_variantes_dun_meme_nom():
    assert prospection._normaliser("Boulangerie Martin") == prospection._normaliser("BOULANGERIE  MARTIN")
    assert prospection._normaliser("SARL Dupont & Fils") == prospection._normaliser("SARL Dupont Fils")


def test_normalisation_distingue_deux_entreprises():
    assert prospection._normaliser("Boulangerie Martin") != prospection._normaliser("Boulangerie Durand")


# ─────────────────────────────────────────────────────────────────
# Construction du lead — traçabilité
# ─────────────────────────────────────────────────────────────────
def test_lead_conserve_source_horodatage_et_base_legale():
    lead = prospection._lead_depuis(
        {"nom": "Café du Port", "siret": "12345678900011", "ville": "Nantes",
         "source": "google-places", "source_url": "https://cafeduport.fr"},
        {"email": "marie.dupont@cafeduport.fr", "activite": "café restaurant"},
        72, ["Coordonnées de contact trouvées"], ICP_TEST,
    )
    assert lead["source_url"] == "https://cafeduport.fr"
    assert lead["base_legale"] == "interet_legitime_prospection_b2b"
    assert lead["collecte_le"]
    assert lead["email_nominatif"] is True
    assert lead["information_envoyee"] is False


def test_lead_reste_compatible_avec_le_pipeline_croissance():
    """growth.py lit ces champs : les casser sortirait les prospects du pipeline."""
    lead = prospection._lead_depuis(
        {"nom": "Test", "source": "recherche-entreprises"}, {}, 50, [], ICP_TEST)
    for champ in ("id", "name", "company", "email", "sub", "snippet", "source", "stage", "campaign"):
        assert champ in lead
    assert lead["stage"] == "detected"


def test_adresse_generique_non_marquee_nominative():
    lead = prospection._lead_depuis(
        {"nom": "Boulangerie", "source": "google-places"},
        {"email": "contact@boulangerie.fr"}, 60, [], ICP_TEST)
    assert lead["email_nominatif"] is False
