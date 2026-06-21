"""
Heyzine Vision Book integration.
Génère un PDF « Vision Book » magazine premium (couverture + vision + piliers +
valeurs + analyse IA + SWOT + roadmap), l'héberge en URL publique, puis le
convertit en flipbook Heyzine (https://heyzine.com/api1/rest).
"""
import os
import uuid
from pathlib import Path
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas

from vision_board import compute_analysis, DEFAULT_VISION_INFO

HEYZINE_REST_ENDPOINT = "https://heyzine.com/api1/rest"
FILES_DIR = Path(__file__).parent / "visionbook_files"
FILES_DIR.mkdir(exist_ok=True)

NAVY = colors.HexColor("#0B1F3A")
NAVY2 = colors.HexColor("#163D57")
NAVY3 = colors.HexColor("#0e2a45")
GOLD = colors.HexColor("#D6A85F")
GOLD_SOFT = colors.HexColor("#2a2415")
CREAM = colors.HexColor("#F6F2EA")
MUTED = colors.HexColor("#9fb2c9")
MINT = colors.HexColor("#34d399")
WHITE = colors.white

W, H = A4
MX = 22 * mm  # marge gauche/droite


def _wrap(c, text, x, y, width, font="Helvetica", size=11, leading=15, color=colors.black):
    c.setFillColor(color); c.setFont(font, size)
    line = ""
    for w in (text or "").split():
        test = (line + " " + w).strip()
        if c.stringWidth(test, font, size) > width:
            c.drawString(x, y, line); y -= leading; line = w
        else:
            line = test
    if line:
        c.drawString(x, y, line); y -= leading
    return y


def _bg(c):
    c.setFillColor(NAVY); c.rect(0, 0, W, H, fill=1, stroke=0)
    # subtle gold glow top-right
    c.setFillColor(NAVY3); c.circle(W + 20 * mm, H - 10 * mm, 70 * mm, fill=1, stroke=0)


def _header(c, kicker, page_no=None):
    c.setFillColor(NAVY2); c.rect(0, H - 18 * mm, W, 18 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD); c.rect(0, H - 18 * mm, W, 1.2 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 9)
    c.drawString(MX, H - 11.5 * mm, kicker.upper())
    c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawRightString(W - MX, H - 11.5 * mm, "MYEXTENSION AI · VISION BOOK")
    if page_no:
        c.setFillColor(MUTED); c.setFont("Helvetica", 8)
        c.drawCentredString(W / 2, 10 * mm, str(page_no))


def _title(c, text, y):
    c.setFillColor(CREAM); c.setFont("Helvetica-Bold", 22)
    c.drawString(MX, y, text)
    c.setFillColor(GOLD); c.rect(MX, y - 5 * mm, 26 * mm, 1.4 * mm, fill=1, stroke=0)
    return y - 16 * mm


def _card(c, x, y, w, h, fill=NAVY2, radius=4 * mm, border=None):
    c.setFillColor(fill)
    c.roundRect(x, y - h, w, h, radius, fill=1, stroke=0)
    if border:
        c.setStrokeColor(border); c.setLineWidth(0.8)
        c.roundRect(x, y - h, w, h, radius, fill=0, stroke=1)


def _bar(c, x, y, w, pct, color=GOLD, bg=colors.HexColor("#22344b"), h=4):
    c.setFillColor(bg); c.roundRect(x, y, w, h, h / 2, fill=1, stroke=0)
    c.setFillColor(color); c.roundRect(x, y, max(2, w * pct / 100), h, h / 2, fill=1, stroke=0)


def build_visionbook_pdf(board: dict, info: dict, analysis: dict, path: Path):
    c = pdfcanvas.Canvas(str(path), pagesize=A4)
    obj = info.get("objectifs", {}) or {}
    scores = analysis.get("scores", {})
    swot = analysis.get("swot", {})

    # ============ PAGE 1 — COVER ============
    _bg(c)
    c.setFillColor(GOLD); c.rect(0, H * 0.60, W, 1.6 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 11)
    c.drawString(MX, H * 0.70, "MYEXTENSION AI  ·  VISION BOOK")
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 34)
    c.drawString(MX, H * 0.535, board.get("title", "Ma Vision"))
    _wrap(c, info.get("mission", ""), MX, H * 0.47, W - 2 * MX,
          font="Helvetica", size=13, leading=20, color=CREAM)
    # mini score badge
    g = scores.get("global", 0)
    c.setFillColor(NAVY2); c.roundRect(MX, H * 0.30 - 26 * mm, 60 * mm, 26 * mm, 4 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD); c.setFont("Helvetica", 8); c.drawString(MX + 6 * mm, H * 0.30 - 8 * mm, "SCORE DE VISION (IA)")
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 26); c.drawString(MX + 6 * mm, H * 0.30 - 21 * mm, f"{g}/100")
    c.setFillColor(GOLD); c.setFont("Helvetica-Oblique", 11)
    c.drawString(MX, 20 * mm, "« Construisez votre futur avant de le vivre. »")
    c.showPage()

    # ============ PAGE 2 — VISION & OBJECTIFS ============
    _bg(c); _header(c, "Vision & Objectifs", 2)
    y = _title(c, "Ma trajectoire", H - 32 * mm)
    for label, key in [("Vision · 1 an", "vision_1an"), ("Vision · 3 ans", "vision_3ans"),
                       ("Vision · 10 ans", "vision_10ans")]:
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 11); c.drawString(MX, y, label); y -= 6 * mm
        y = _wrap(c, info.get(key, ""), MX, y, W - 2 * MX, size=11, leading=15, color=CREAM); y -= 7 * mm
    # KPI tiles
    y -= 2 * mm
    kpis = [("OBJECTIF CA", f"{int(obj.get('ca_cible', 0)):,} EUR".replace(",", " "), 58),
            ("MARGE OP.", f"{obj.get('marge_op_pct', '-')}%", obj.get('marge_op_pct', 0)),
            ("CLIENTS", str(obj.get("nb_clients", "-")), 65),
            ("IKIGAI", f"{obj.get('ikigai_score', '-')}/100", obj.get('ikigai_score', 0))]
    bw = (W - 2 * MX - 3 * 5 * mm) / 4
    for i, (k, v, p) in enumerate(kpis):
        bx = MX + i * (bw + 5 * mm)
        _card(c, bx, y, bw, 30 * mm, fill=NAVY2)
        c.setFillColor(GOLD); c.setFont("Helvetica", 7); c.drawString(bx + 4 * mm, y - 7 * mm, k)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 13); c.drawString(bx + 4 * mm, y - 16 * mm, v)
        _bar(c, bx + 4 * mm, y - 24 * mm, bw - 8 * mm, min(100, p))
    y -= 30 * mm
    # Phase
    phase = obj.get("phase", {}) or {}
    y -= 8 * mm
    _card(c, MX, y, W - 2 * MX, 20 * mm, fill=NAVY3, border=GOLD)
    c.setFillColor(GOLD); c.setFont("Helvetica", 8); c.drawString(MX + 6 * mm, y - 7 * mm, "PHASE ACTUELLE")
    c.setFillColor(CREAM); c.setFont("Helvetica-Bold", 14)
    c.drawString(MX + 6 * mm, y - 15 * mm, f"{phase.get('label', 'Lancement')} — Mois {phase.get('mois', 4)}/{phase.get('total', 12)}")
    _bar(c, MX + 80 * mm, y - 12 * mm, W - 2 * MX - 86 * mm,
         (phase.get('mois', 4) / max(1, phase.get('total', 12))) * 100, color=MINT)
    c.showPage()

    # ============ PAGE 3 — STRATEGIC PILLARS ============
    _bg(c); _header(c, "Strategic Pillars", 3)
    y = _title(c, "Mes piliers de vie", H - 32 * mm)
    piliers = info.get("piliers") or []
    cw = (W - 2 * MX - 5 * mm) / 2
    for i, p in enumerate(piliers[:6]):
        col = i % 2; row = i // 2
        px = MX + col * (cw + 5 * mm)
        py = y - row * 33 * mm
        _card(c, px, py, cw, 28 * mm, fill=NAVY2)
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 12); c.drawString(px + 5 * mm, py - 8 * mm, p.get("label", ""))
        _wrap(c, p.get("text", ""), px + 5 * mm, py - 14 * mm, cw - 10 * mm, size=9.5, leading=12, color=CREAM)
        c.setFillColor(MUTED); c.setFont("Helvetica", 8); c.drawString(px + 5 * mm, py - 24 * mm, f"{p.get('progress', 0)}% atteint")
        _bar(c, px + 25 * mm, py - 25 * mm, cw - 30 * mm, p.get("progress", 0))
    c.showPage()

    # ============ PAGE 4 — CORE VALUES ============
    _bg(c); _header(c, "Core Values", 4)
    y = _title(c, "Mes valeurs fondatrices", H - 32 * mm)
    for v in (info.get("valeurs") or []):
        _card(c, MX, y, W - 2 * MX, 14 * mm, fill=NAVY2)
        c.setFillColor(GOLD); c.circle(MX + 8 * mm, y - 7 * mm, 2 * mm, fill=1, stroke=0)
        c.setFillColor(CREAM); c.setFont("Helvetica-Bold", 14); c.drawString(MX + 16 * mm, y - 9 * mm, v)
        c.setFillColor(MUTED); c.setFont("Helvetica", 9)
        c.drawRightString(W - MX - 6 * mm, y - 9 * mm, "Alignée à la vision")
        y -= 18 * mm
    c.showPage()

    # ============ PAGE 5 — ANALYSE IA ============
    _bg(c); _header(c, "Analyse IA · Assistant Vision", 5)
    y = _title(c, "Analyse de ma vision", H - 32 * mm)
    c.setFillColor(MUTED); c.setFont("Helvetica-Oblique", 9)
    c.drawString(MX, y + 6 * mm, "Généré par l'Assistant Vision AI · MyExtension AI")
    for lbl, key in [("Clarté", "clarte"), ("Alignement", "alignement"), ("Ambition", "ambition"),
                     ("Faisabilité", "faisabilite"), ("Équilibre", "equilibre")]:
        val = scores.get(key, 0)
        c.setFillColor(CREAM); c.setFont("Helvetica", 11); c.drawString(MX, y, lbl)
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 11); c.drawRightString(W - MX, y, f"{val}%")
        _bar(c, MX, y - 4 * mm, W - 2 * MX, val, color=MINT, h=5)
        y -= 13 * mm
    # global + verdict
    y -= 4 * mm
    _card(c, MX, y, W - 2 * MX, 26 * mm, fill=NAVY3, border=GOLD)
    c.setFillColor(GOLD); c.setFont("Helvetica", 8); c.drawString(MX + 6 * mm, y - 7 * mm, "SCORE GLOBAL")
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 24)
    c.drawString(MX + 6 * mm, y - 19 * mm, f"{scores.get('global', 0)} / 100")
    c.setFillColor(MINT); c.setFont("Helvetica-Bold", 12)
    c.drawRightString(W - MX - 6 * mm, y - 11 * mm, f"Verdict : {analysis.get('verdict', '')}")
    c.setFillColor(MUTED)
    _wrap(c, analysis.get("message", ""), MX + 70 * mm, y - 17 * mm, W - 2 * MX - 76 * mm,
          size=8.5, leading=11, color=MUTED)
    c.showPage()

    # ============ PAGE 6 — SWOT (2x2) ============
    _bg(c); _header(c, "Analyse SWOT · IA", 6)
    y = _title(c, "Forces · Faiblesses · Opportunités · Menaces", H - 32 * mm)
    quad = [("FORCES", swot.get("forces", []), MINT),
            ("FAIBLESSES", swot.get("faiblesses", []), GOLD),
            ("OPPORTUNITÉS", swot.get("opportunites", []), MINT),
            ("MENACES", swot.get("menaces", []), GOLD)]
    qw = (W - 2 * MX - 5 * mm) / 2
    qh = 52 * mm
    for i, (lbl, items, col) in enumerate(quad):
        cx = MX + (i % 2) * (qw + 5 * mm)
        cy = y - (i // 2) * (qh + 5 * mm)
        _card(c, cx, cy, qw, qh, fill=NAVY2, border=col)
        c.setFillColor(col); c.setFont("Helvetica-Bold", 11); c.drawString(cx + 6 * mm, cy - 9 * mm, lbl)
        yy = cy - 17 * mm
        for it in items[:4]:
            c.setFillColor(col); c.setFont("Helvetica", 9); c.drawString(cx + 6 * mm, yy, "•")
            yy = _wrap(c, it, cx + 10 * mm, yy, qw - 14 * mm, size=9, leading=12, color=CREAM) - 2
    c.showPage()

    # ============ PAGE 7 — CONSEILS & OPPORTUNITÉS ============
    _bg(c); _header(c, "Plan d'action · IA", 7)
    y = _title(c, "Conseils du Co-pilote", H - 32 * mm)
    for i, ad in enumerate(analysis.get("conseils", []), 1):
        _card(c, MX, y, W - 2 * MX, 18 * mm, fill=NAVY2)
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 13); c.drawString(MX + 6 * mm, y - 11 * mm, str(i))
        _wrap(c, ad, MX + 16 * mm, y - 7 * mm, W - 2 * MX - 22 * mm, size=10, leading=13, color=CREAM)
        y -= 22 * mm
    y -= 4 * mm
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 12); c.drawString(MX, y, "Opportunités business"); y -= 9 * mm
    for op in analysis.get("opportunites_business", []):
        c.setFillColor(MINT); c.setFont("Helvetica", 10); c.drawString(MX, y, "✦")
        y = _wrap(c, op, MX + 6 * mm, y, W - 2 * MX - 6 * mm, size=10, leading=13, color=CREAM) - 3
    c.showPage()

    c.save()


def build_router(db: AsyncIOMotorDatabase) -> APIRouter:
    router = APIRouter(prefix="/vision", tags=["vision-book"])
    COLLECTION = db.vision_boards
    BOOKS = db.vision_books
    client_id = os.environ.get("HEYZINE_CLIENT_ID", "")
    base_url = os.environ.get("APP_BASE_URL", "").rstrip("/")

    async def _board_and_info(user_id="demo"):
        doc = await COLLECTION.find_one({"user_id": user_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Vision Board introuvable")
        info = doc.get("vision_info") or DEFAULT_VISION_INFO()
        return doc, info

    async def _host_pdf_publicly(pdf_path: Path) -> str:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
            files = {"file": (pdf_path.name, pdf_path.read_bytes(), "application/pdf")}
            r = await client.post("https://tmpfiles.org/api/v1/upload", files=files)
            r.raise_for_status()
            url = r.json()["data"]["url"]
        return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")

    @router.post("/visionbook/generate")
    async def generate_visionbook(user_id: str = "demo"):
        """Génère le PDF Vision Book (avec analyse IA) puis le convertit en flipbook Heyzine."""
        doc, info = await _board_and_info(user_id)
        analysis = compute_analysis(info)
        book_id = uuid.uuid4().hex[:12]
        pdf_path = FILES_DIR / f"{book_id}.pdf"
        build_visionbook_pdf(doc, info, analysis, pdf_path)

        local_pdf_url = f"{base_url}/api/vision/visionbook/file/{book_id}.pdf"
        flipbook_url, thumb = None, None
        heyzine_error = None
        try:
            public_url = await _host_pdf_publicly(pdf_path)
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                resp = await client.post(
                    HEYZINE_REST_ENDPOINT,
                    data={"pdf": public_url, "k": client_id,
                          "title": doc.get("title", "Vision Book"),
                          "subtitle": "MyExtension AI · Vision Book"},
                )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") is False:
                    heyzine_error = data.get("msg", "Conversion refusée")
                else:
                    flipbook_url = data.get("url") or data.get("custom")
                    thumb = data.get("thumbnail")
            else:
                heyzine_error = f"Heyzine {resp.status_code}: {resp.text[:200]}"
        except Exception as e:  # noqa
            heyzine_error = str(e)

        record = {
            "id": book_id, "user_id": user_id,
            "pdf_url": local_pdf_url, "flipbook_url": flipbook_url, "thumbnail": thumb,
            "title": doc.get("title"), "heyzine_error": heyzine_error,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await BOOKS.update_one({"user_id": user_id}, {"$set": record}, upsert=True)
        if not flipbook_url:
            raise HTTPException(502, detail=heyzine_error or "Conversion Heyzine échouée")
        return record

    @router.api_route("/visionbook/file/{filename}", methods=["GET", "HEAD"])
    async def serve_pdf(filename: str):
        safe = os.path.basename(filename)
        path = FILES_DIR / safe
        if not path.exists():
            raise HTTPException(404, "PDF introuvable")
        return FileResponse(str(path), media_type="application/pdf")

    @router.get("/visionbook")
    async def latest_visionbook(user_id: str = "demo"):
        rec = await BOOKS.find_one({"user_id": user_id}, {"_id": 0})
        return rec or {}

    return router
