"""Espace vendeur — dépôt de produits multi-vendeurs et publication Shopify.

Zayado est une marketplace : plusieurs vendeurs indépendants déposent leurs
produits, Zayado modère, puis le produit part dans la boutique Shopify.

Le cycle d'un produit
─────────────────────
    brouillon  →  en_attente  →  publie
                      ↓
                   refuse  →  (le vendeur corrige, resoumet)

  • brouillon   le vendeur travaille sa fiche, personne d'autre ne la voit
  • en_attente  soumis à Zayado, plus modifiable par le vendeur
  • publie      créé dans Shopify, l'identifiant Shopify est conservé
  • refuse      motif obligatoire, le vendeur peut corriger et resoumettre

Pourquoi une modération et pas une publication directe
──────────────────────────────────────────────────────
Une marketplace engage sa réputation sur chaque fiche publiée. Un produit
publié directement par un vendeur inconnu peut être hors-charte, mal décrit,
ou illégal — et c'est Zayado qui répond. Le passage par `en_attente` est donc
structurel, pas une étape administrative qu'on pourrait sauter.

Ce que ce module NE fait PAS
───────────────────────────
Il ne touche pas au paiement. Shopify sert de catalogue et de vitrine ; le
tunnel d'achat est décidé ailleurs. Chaque produit publié porte le tag
`zayado-vendeur` et un metafield `zayado.produit_id`, ce qui permet de le
retrouver et de le rattacher plus tard, quel que soit le choix de tunnel.
"""
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User

from routes.missing_apis import (
    _ensure_table, _list_rows, _insert_row, _update_row, _delete_row,
)
from routes.growth import _get_kv, _save_kv

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vendeur", tags=["vendeur"])

TABLE = "vendor_products"
CLE_PROFIL = "vendeur_profil"

# ── Shopify ──────────────────────────────────────────────────────
# Le domaine technique (xxxxx.myshopify.com), PAS le domaine public.
SHOPIFY_BOUTIQUE = (os.environ.get("SHOPIFY_SHOP_DOMAIN", "") or "").replace("https://", "").strip("/")
SHOPIFY_TOKEN = os.environ.get("SHOPIFY_ADMIN_TOKEN", "")
# Version d'API figée par variable : Shopify en sort une par trimestre et
# retire les anciennes. Épingler évite qu'une publication casse sans prévenir.
SHOPIFY_VERSION = os.environ.get("SHOPIFY_API_VERSION", "2025-01")
# Où pointe le produit pour l'achat réel. Vide = le produit reste achetable
# dans Shopify. Rempli = la fiche renvoie vers cette base d'URL.
ZAYADO_LIEN_ACHAT = os.environ.get("ZAYADO_PRODUCT_URL_BASE", "").rstrip("/")

STATUTS = ("brouillon", "en_attente", "publie", "refuse")
MAX_IMAGES = 6


def _maintenant() -> str:
    return datetime.now(timezone.utc).isoformat()


def _shopify_pret() -> bool:
    return bool(SHOPIFY_BOUTIQUE and SHOPIFY_TOKEN)


# ─────────────────────────────────────────────────────────────────
# Validation — refuser tôt plutôt que d'échouer chez Shopify
# ─────────────────────────────────────────────────────────────────
def _valider(produit: dict) -> list[str]:
    """Renvoie la liste des problèmes, en langage clair pour le vendeur.

    On valide ici plutôt que de laisser Shopify refuser : ses messages
    d'erreur sont en anglais et parlent de son modèle de données, pas du
    formulaire que le vendeur a sous les yeux.
    """
    erreurs = []
    titre = (produit.get("titre") or "").strip()
    if len(titre) < 3:
        erreurs.append("Le nom du produit doit faire au moins 3 caractères.")
    if len(titre) > 255:
        erreurs.append("Le nom du produit dépasse 255 caractères.")

    description = re.sub(r"<[^>]+>", "", produit.get("description") or "").strip()
    if len(description) < 30:
        erreurs.append("La description doit faire au moins 30 caractères — c'est ce qui décide l'achat.")

    try:
        prix = float(str(produit.get("prix", "")).replace(",", "."))
        if prix <= 0:
            erreurs.append("Le prix doit être supérieur à 0.")
    except (TypeError, ValueError):
        erreurs.append("Le prix n'est pas un nombre valide.")

    stock = produit.get("stock")
    if stock not in (None, ""):
        try:
            if int(stock) < 0:
                erreurs.append("Le stock ne peut pas être négatif.")
        except (TypeError, ValueError):
            erreurs.append("Le stock doit être un nombre entier.")

    images = produit.get("images") or []
    if not isinstance(images, list) or not images:
        erreurs.append("Ajoutez au moins une image — un produit sans photo ne se vend pas.")
    elif len(images) > MAX_IMAGES:
        erreurs.append(f"{MAX_IMAGES} images maximum.")
    else:
        for url in images:
            if not str(url).startswith(("http://", "https://")):
                erreurs.append("Chaque image doit être une adresse web complète (https://…).")
                break
    return erreurs


# ─────────────────────────────────────────────────────────────────
# Appel Shopify
# ─────────────────────────────────────────────────────────────────
MUTATION_PRODUIT = """
mutation creerProduit($product: ProductSetInput!) {
  productSet(synchronous: true, input: $product) {
    product { id handle title status onlineStoreUrl }
    userErrors { field message }
  }
}
"""


async def _appel_shopify(requete: str, variables: dict) -> dict:
    """Appelle l'API Admin GraphQL. Lève une HTTPException lisible en cas d'échec.

    Les erreurs de Shopify remontent telles quelles jusqu'à l'écran : une
    publication qui échoue en silence est le pire cas possible ici — le vendeur
    croit son produit en ligne alors qu'il n'existe nulle part.
    """
    if not _shopify_pret():
        raise HTTPException(503, "Shopify n'est pas configuré : SHOPIFY_SHOP_DOMAIN et SHOPIFY_ADMIN_TOKEN manquent côté serveur.")
    url = f"https://{SHOPIFY_BOUTIQUE}/admin/api/{SHOPIFY_VERSION}/graphql.json"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, headers={
                "X-Shopify-Access-Token": SHOPIFY_TOKEN,
                "Content-Type": "application/json",
            }, json={"query": requete, "variables": variables})
    except Exception as e:
        logger.warning("Shopify injoignable: %s", e)
        raise HTTPException(503, "Shopify est injoignable pour l'instant. Réessayez dans un instant.")

    if r.status_code == 401:
        raise HTTPException(502, "Shopify a refusé le jeton d'accès. Vérifiez SHOPIFY_ADMIN_TOKEN et les autorisations de l'application.")
    if r.status_code == 404:
        raise HTTPException(502, f"Boutique ou version d'API introuvable ({SHOPIFY_BOUTIQUE}, {SHOPIFY_VERSION}).")
    if r.status_code >= 400:
        raise HTTPException(502, f"Shopify a répondu {r.status_code}. Détail : {r.text[:300]}")

    data = r.json()
    if data.get("errors"):
        messages = "; ".join(e.get("message", "") for e in data["errors"])
        raise HTTPException(502, f"Shopify a rejeté la requête : {messages[:400]}")
    return data.get("data") or {}


def _entree_shopify(produit: dict, vendeur: str) -> dict:
    """Traduit une fiche Zayado en entrée Shopify."""
    prix = f"{float(str(produit.get('prix', 0)).replace(',', '.')):.2f}"
    description = produit.get("description") or ""
    if ZAYADO_LIEN_ACHAT:
        lien = f"{ZAYADO_LIEN_ACHAT}/{produit['id']}"
        description += (
            f'\n<p><a href="{lien}" rel="noopener">Voir la fiche complète et commander sur Zayado</a></p>'
        )

    entree = {
        "title": produit.get("titre"),
        "descriptionHtml": description,
        "vendor": vendeur or "Vendeur Zayado",
        "productType": produit.get("categorie") or "",
        # Le tag rend tous les produits vendeurs filtrables dans l'admin Shopify.
        "tags": ["zayado-vendeur", f"vendeur-{re.sub(r'[^a-z0-9-]', '-', (vendeur or 'inconnu').lower())[:40]}"],
        # DRAFT volontaire : la fiche arrive dans Shopify sans être publiée sur
        # la vitrine. Zayado garde la main sur le moment de la mise en ligne.
        "status": "DRAFT",
        "productOptions": [{"name": "Titre", "values": [{"name": "Default Title"}]}],
        "variants": [{
            "price": prix,
            "optionValues": [{"optionName": "Titre", "name": "Default Title"}],
            **({"sku": produit["sku"]} if produit.get("sku") else {}),
        }],
        "metafields": [{
            "namespace": "zayado",
            "key": "produit_id",
            "type": "single_line_text_field",
            "value": produit["id"],
        }],
    }
    images = produit.get("images") or []
    if images:
        entree["files"] = [{"originalSource": url, "contentType": "IMAGE"} for url in images[:MAX_IMAGES]]
    return entree


# ─────────────────────────────────────────────────────────────────
# Profil vendeur
# ─────────────────────────────────────────────────────────────────
PROFIL_DEFAUT = {
    "nom_boutique": "",
    "description": "",
    "email_contact": "",
    "telephone": "",
    "siret": "",
    "site": "",
    "conditions_acceptees": False,
}


@router.get("/profil")
async def lire_profil(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    enregistre = await _get_kv(db, user.id, CLE_PROFIL) or {}
    return {**PROFIL_DEFAUT, **enregistre}


@router.put("/profil")
async def ecrire_profil(patch: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    actuel = await _get_kv(db, user.id, CLE_PROFIL) or {}
    fusion = {**PROFIL_DEFAUT, **actuel, **(patch or {})}
    await _save_kv(db, user.id, CLE_PROFIL, fusion)
    return fusion


@router.get("/etat")
async def etat(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Ce que le vendeur doit savoir avant de déposer quoi que ce soit."""
    profil = {**PROFIL_DEFAUT, **(await _get_kv(db, user.id, CLE_PROFIL) or {})}
    produits = await _list_rows(db, TABLE, user.id)
    compte = {s: 0 for s in STATUTS}
    for p in produits:
        compte[p.get("statut", "brouillon")] = compte.get(p.get("statut", "brouillon"), 0) + 1
    return {
        "profil_complet": bool(profil.get("nom_boutique") and profil.get("email_contact") and profil.get("conditions_acceptees")),
        "profil": profil,
        "compteurs": compte,
        "shopify": {
            "configure": _shopify_pret(),
            "boutique": SHOPIFY_BOUTIQUE or None,
            "version_api": SHOPIFY_VERSION,
            "manque": "" if _shopify_pret() else "Variables SHOPIFY_SHOP_DOMAIN et SHOPIFY_ADMIN_TOKEN absentes côté serveur.",
        },
        "limites": {"images_max": MAX_IMAGES},
    }


# ─────────────────────────────────────────────────────────────────
# Produits du vendeur
# ─────────────────────────────────────────────────────────────────
class ProduitIn(BaseModel):
    titre: str
    description: Optional[str] = ""
    prix: Optional[str] = "0"
    stock: Optional[int] = None
    sku: Optional[str] = None
    categorie: Optional[str] = None
    images: Optional[list[str]] = None


@router.get("/produits")
async def lister(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    produits = await _list_rows(db, TABLE, user.id)
    produits.sort(key=lambda p: p.get("maj_le") or p.get("created_at") or "", reverse=True)
    return {"items": produits}


@router.post("/produits")
async def creer(body: ProduitIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profil = {**PROFIL_DEFAUT, **(await _get_kv(db, user.id, CLE_PROFIL) or {})}
    if not profil.get("nom_boutique"):
        raise HTTPException(400, "Renseignez d'abord le nom de votre boutique dans votre profil vendeur.")
    donnees = body.dict()
    donnees.update({
        "statut": "brouillon",
        "vendeur": profil["nom_boutique"],
        "maj_le": _maintenant(),
        "shopify_id": "",
        "motif_refus": "",
    })
    return await _insert_row(db, TABLE, user.id, donnees)


@router.put("/produits/{pid}")
async def modifier(pid: str, body: ProduitIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    produits = await _list_rows(db, TABLE, user.id)
    actuel = next((p for p in produits if p.get("id") == pid), None)
    if not actuel:
        raise HTTPException(404, "Produit introuvable.")
    if actuel.get("statut") == "en_attente":
        raise HTTPException(409, "Ce produit est en cours de vérification : il n'est plus modifiable. Attendez la réponse de Zayado.")
    patch = body.dict()
    patch["maj_le"] = _maintenant()
    # Un produit déjà publié qui change repasse en vérification : sinon un
    # vendeur pourrait faire valider un produit anodin puis le remplacer.
    if actuel.get("statut") == "publie":
        patch["statut"] = "en_attente"
    elif actuel.get("statut") == "refuse":
        patch["statut"] = "brouillon"
        patch["motif_refus"] = ""   # "" et non None : _update_row ignore les None
    return await _update_row(db, TABLE, user.id, pid, patch)


@router.delete("/produits/{pid}")
async def supprimer(pid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ok = await _delete_row(db, TABLE, user.id, pid)
    if not ok:
        raise HTTPException(404, "Produit introuvable.")
    return {"supprime": True}


@router.post("/produits/{pid}/soumettre")
async def soumettre(pid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Le vendeur envoie sa fiche à la vérification Zayado."""
    produits = await _list_rows(db, TABLE, user.id)
    produit = next((p for p in produits if p.get("id") == pid), None)
    if not produit:
        raise HTTPException(404, "Produit introuvable.")
    erreurs = _valider(produit)
    if erreurs:
        raise HTTPException(422, {"message": "La fiche est incomplète.", "erreurs": erreurs})
    return await _update_row(db, TABLE, user.id, pid, {
        "statut": "en_attente", "soumis_le": _maintenant(), "motif_refus": "", "maj_le": _maintenant(),
    })


@router.get("/produits/{pid}/verifier")
async def verifier(pid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Dit au vendeur ce qui manque, avant qu'il soumette."""
    produits = await _list_rows(db, TABLE, user.id)
    produit = next((p for p in produits if p.get("id") == pid), None)
    if not produit:
        raise HTTPException(404, "Produit introuvable.")
    erreurs = _valider(produit)
    return {"pret": not erreurs, "erreurs": erreurs}


# ─────────────────────────────────────────────────────────────────
# Modération Zayado
# ─────────────────────────────────────────────────────────────────
async def _exiger_admin(user: User):
    if (getattr(user, "role", "") or "") not in ("admin", "super_admin"):
        raise HTTPException(403, "Réservé à l'équipe Zayado.")


@router.get("/moderation/attente")
async def file_moderation(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _exiger_admin(user)
    await _ensure_table(db, TABLE)
    r = await db.execute(text(f"SELECT id, user_id, data FROM {TABLE} ORDER BY created_at DESC"))
    sortie = []
    for ligne in r.fetchall():
        donnees = ligne[2]
        if isinstance(donnees, str):
            try:
                donnees = json.loads(donnees)
            except Exception:
                continue
        if (donnees or {}).get("statut") == "en_attente":
            donnees["_vendeur_user_id"] = ligne[1]
            sortie.append(donnees)
    return {"items": sortie}


class DecisionIn(BaseModel):
    vendeur_user_id: str
    motif: Optional[str] = None


@router.post("/moderation/{pid}/publier")
async def publier(pid: str, body: DecisionIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Valide la fiche et la crée réellement dans Shopify.

    L'ordre compte : on appelle Shopify AVANT de marquer le produit publié.
    L'inverse laisserait des fiches marquées « en ligne » qui n'existent nulle
    part — l'erreur la plus coûteuse à rattraper sur une marketplace.
    """
    await _exiger_admin(user)
    produits = await _list_rows(db, TABLE, body.vendeur_user_id)
    produit = next((p for p in produits if p.get("id") == pid), None)
    if not produit:
        raise HTTPException(404, "Produit introuvable.")
    erreurs = _valider(produit)
    if erreurs:
        raise HTTPException(422, {"message": "La fiche ne passe pas la validation.", "erreurs": erreurs})

    data = await _appel_shopify(MUTATION_PRODUIT, {"product": _entree_shopify(produit, produit.get("vendeur", ""))})
    resultat = (data.get("productSet") or {})
    fautes = resultat.get("userErrors") or []
    if fautes:
        detail = "; ".join(f"{'/'.join(f.get('field') or [])}: {f.get('message')}" for f in fautes)
        raise HTTPException(422, f"Shopify a refusé la fiche : {detail[:400]}")
    cree = resultat.get("product") or {}
    if not cree.get("id"):
        raise HTTPException(502, "Shopify n'a pas renvoyé d'identifiant produit. Rien n'a été marqué publié.")

    return await _update_row(db, TABLE, body.vendeur_user_id, pid, {
        "statut": "publie",
        "shopify_id": cree["id"],
        "shopify_handle": cree.get("handle"),
        "publie_le": _maintenant(),
        "motif_refus": "",
        "maj_le": _maintenant(),
    })


@router.post("/moderation/{pid}/refuser")
async def refuser(pid: str, body: DecisionIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _exiger_admin(user)
    if not (body.motif or "").strip():
        # Un refus sans motif est ingérable pour le vendeur : il ne sait pas
        # quoi corriger et resoumet à l'identique.
        raise HTTPException(400, "Un motif de refus est obligatoire.")
    maj = await _update_row(db, TABLE, body.vendeur_user_id, pid, {
        "statut": "refuse", "motif_refus": body.motif.strip(), "maj_le": _maintenant(),
    })
    if not maj:
        raise HTTPException(404, "Produit introuvable.")
    return maj
