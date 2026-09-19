"""
Factures & Dépenses — Pilotage.jsx. Réutilise les helpers génériques déjà
en place dans routes/missing_apis.py (_list_rows/_insert_row/_update_row/
_delete_row), même table pattern JSON que le reste du backend — zéro code
dupliqué, zéro nouvelle dépendance.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User
from routes.missing_apis import _list_rows, _insert_row, _update_row, _delete_row

router = APIRouter(prefix="/api", tags=["Finances"])


class FactureIn(BaseModel):
    client: str
    reference: str = ""
    montant: float
    statut: str = "À envoyer"
    echeance: str = ""


class DepenseIn(BaseModel):
    libelle: str
    categorie: str = "SaaS"
    montant: float
    date: str = ""


@router.get("/factures")
async def list_factures(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _list_rows(db, "user_factures", user.id)


@router.post("/factures")
async def create_facture(body: FactureIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _insert_row(db, "user_factures", user.id, body.dict())


@router.put("/factures/{fid}")
async def update_facture(fid: str, body: FactureIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await _update_row(db, "user_factures", user.id, fid, body.dict())
    if not result:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    return result


@router.delete("/factures/{fid}")
async def delete_facture(fid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _delete_row(db, "user_factures", user.id, fid)
    return {"ok": True}


@router.get("/depenses")
async def list_depenses(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _list_rows(db, "user_depenses", user.id)


@router.post("/depenses")
async def create_depense(body: DepenseIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _insert_row(db, "user_depenses", user.id, body.dict())


@router.delete("/depenses/{did}")
async def delete_depense(did: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _delete_row(db, "user_depenses", user.id, did)
    return {"ok": True}
