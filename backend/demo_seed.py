"""Seed de démonstration pour le compte de test unique « Thomas ».

Objectif : rendre l'application vivante et « investor-ready » sur n'importe quel
environnement (preview ET Railway) SANS jamais fabriquer de fausses métriques
pour de vrais utilisateurs. Le peuplement ne s'applique QU'au compte de test
thomas@zayado.fr, et il est idempotent (ne s'exécute qu'une fois).

Tables peuplées (schémas vérifiés) :
  - wellness_checkins  → streak + score d'énergie (Cockpit / Bien-être)
  - user_tasks (JSON)  → missions + progrès de la semaine + priorité du jour
  - conversations      → interactions IA (ROI « Valeur générée »)
  - finance_entries    → CA / trésorerie (Pilotage + Cockpit)
  - user_leads (JSON)  → prospects / pipeline (Croissance)
"""
import json
import uuid
import logging
import datetime as dt

from sqlalchemy import text

logger = logging.getLogger("demo_seed")

DEMO_EMAIL = "thomas@zayado.fr"


def _uid():
    return str(uuid.uuid4())


async def _count(db, table, user_id):
    try:
        r = (await db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE user_id = :uid"), {"uid": user_id})).scalar()
        return int(r or 0)
    except Exception:
        return 0


async def ensure_thomas_demo(db, user):
    """Peuple le compte Thomas avec un jeu de données de démo réaliste (idempotent)."""
    try:
        if user is None:
            return
        email = (getattr(user, "email", "") or "").lower()
        if email != DEMO_EMAIL:
            return
        user_id = user.id

        # Prefs de démo : ne jamais bloquer Thomas avec l'onboarding / la checklist
        # (compte de démonstration → cockpit prêt à pitcher). Idempotent.
        try:
            from routes.growth import _get_kv, _save_kv
            cur_prefs = (await _get_kv(db, user_id, "user_prefs")) or {}
            if not cur_prefs.get("cockpit_checklist_dismissed"):
                cur_prefs = {**cur_prefs, "onboarded": True,
                             "cockpit_checklist_dismissed": True, "explored_modules": True}
                await _save_kv(db, user_id, "user_prefs", cur_prefs)
                await db.commit()
        except Exception as ex:
            logger.warning("seed prefs: %s", ex)

        # Idempotence : si des check-ins bien-être existent déjà, on ne refait rien.
        if await _count(db, "wellness_checkins", user_id) > 0:
            return

        now = dt.datetime.utcnow()
        today = dt.date.today()

        # ── 1) Bien-être : 12 jours consécutifs (streak) ────────────────────
        energy_seq = [4, 3, 4, 5, 4, 3, 4, 4, 5, 4, 3, 4]
        mood_seq   = [4, 3, 4, 4, 5, 3, 4, 4, 4, 5, 3, 4]
        stress_seq = [2, 3, 2, 2, 3, 3, 2, 2, 2, 3, 3, 2]
        sleep_seq  = [4, 3, 4, 4, 3, 3, 4, 4, 4, 3, 3, 4]
        for i in range(12):
            d = today - dt.timedelta(days=i)
            e = energy_seq[i]; m = mood_seq[i]; s = stress_seq[i]; sl = sleep_seq[i]
            score = int(min(100, max(0, (e + m + (6 - s) + sl) / 20 * 100)))
            when = dt.datetime(d.year, d.month, d.day, 8, 30)
            try:
                await db.execute(text(
                    "INSERT INTO wellness_checkins (id, user_id, energy, mood, stress, sleep, notes, score, date, created_at) "
                    "VALUES (:id,:uid,:e,:m,:s,:sl,:notes,:score,:date,:ca)"
                ), {"id": _uid(), "uid": user_id, "e": e, "m": m, "s": s, "sl": sl,
                    "notes": None, "score": score, "date": when, "ca": when})
            except Exception as ex:
                logger.warning("seed wellness: %s", ex)
                break

        # ── 2) Missions (user_tasks JSON) ───────────────────────────────────
        tasks = [
            {"label": "Relancer Julie Bernard (proposition envoyée)", "priority": "urgent", "done": False, "days": 0},
            {"label": "Appeler Sophie Martin — découverte", "priority": "normal", "done": False, "days": 0},
            {"label": "Préparer la proposition Tech & You", "priority": "urgent", "done": False, "days": 1},
            {"label": "Publier le post LinkedIn hebdomadaire", "priority": "faible", "done": False, "days": 2},
            {"label": "Envoyer l'étude de cas à Nova Agency", "priority": "normal", "done": True, "days": 1},
            {"label": "Facturer la mission Alpha Studio", "priority": "normal", "done": True, "days": 2},
            {"label": "Mettre à jour le pipeline commercial", "priority": "faible", "done": True, "days": 3},
            {"label": "Bloquer 2h de deep work sur l'offre", "priority": "normal", "done": True, "days": 4},
        ]
        for idx_t, t in enumerate(tasks):
            created = now - dt.timedelta(hours=idx_t * 3 + 1)  # toutes créées cette semaine
            data = {
                "id": _uid(),
                "label": t["label"],
                "priority": t["priority"],
                "done": t["done"],
                "source": "ai" if t["done"] else "manual",
                "category": "growth",
            }
            try:
                await db.execute(text(
                    "INSERT INTO user_tasks (id, user_id, data, created_at, updated_at) "
                    "VALUES (:id,:uid,:d,:c,:u)"
                ), {"id": data["id"], "uid": user_id, "d": json.dumps(data, ensure_ascii=False),
                    "c": created, "u": created})
            except Exception as ex:
                logger.warning("seed tasks: %s", ex)
                break

        # ── 3) Conversations IA (ROI) ───────────────────────────────────────
        conv_titles = [
            "Rédiger un email de relance", "Analyser mon pipeline", "Idées de posts LinkedIn",
            "Structurer mon offre premium", "Préparer un devis", "Répondre à une objection prix",
            "Plan de prospection 30 jours", "Séquence de bienvenue client", "Améliorer ma page de vente",
            "Prioriser ma semaine", "Script d'appel découverte", "Message de closing",
            "Analyser un concurrent", "Résumé de ma réunion", "Optimiser mon tunnel",
        ]
        for i, title in enumerate(conv_titles):
            created = now - dt.timedelta(days=i % 20, hours=(i % 5) + 1)
            msgs = json.dumps([
                {"role": "user", "content": title},
                {"role": "assistant", "content": "Voici une proposition prête à l'emploi…"},
            ], ensure_ascii=False)
            try:
                await db.execute(text(
                    "INSERT INTO conversations (id, user_id, title, mode, messages, is_favorite, shared, total_credits_used, created_at, updated_at) "
                    "VALUES (:id,:uid,:t,:mode,:msgs,:fav,:sh,:cr,:c,:u)"
                ), {"id": _uid(), "uid": user_id, "t": title, "mode": "chat", "msgs": msgs,
                    "fav": False, "sh": False, "cr": 2, "c": created, "u": created})
            except Exception as ex:
                logger.warning("seed conversations: %s", ex)
                break

        # ── 4) Finances (Pilotage / CA) ─────────────────────────────────────
        first_of_month = today.replace(day=1)
        finance = [
            ("revenu", "Coaching pro — Sophie Bernard", 1200, "prestation", 3),
            ("revenu", "Accompagnement — Thomas Leroy", 1100, "prestation", 8),
            ("revenu", "Abonnement annuel — Tech & You", 2300, "abonnement", 12),
            ("revenu", "Site web + SEO — Alpha Studio", 3900, "prestation", 16),
            ("revenu", "Formation IA — Start Learning", 2300, "formation", 20),
            ("depense", "Abonnement outils SaaS", 149, "logiciels", 2),
            ("depense", "Publicité LinkedIn", 320, "marketing", 6),
            ("depense", "Sous-traitance design", 650, "sous-traitance", 10),
            ("depense", "Comptabilité", 180, "administratif", 14),
        ]
        for typ, label, amount, cat, day_off in finance:
            d = first_of_month + dt.timedelta(days=day_off)
            when = dt.datetime(d.year, d.month, min(d.day, 28), 10, 0)
            try:
                await db.execute(text(
                    "INSERT INTO finance_entries (id, user_id, type, label, amount, category, date, recurring, notes, created_at) "
                    "VALUES (:id,:uid,:type,:label,:amount,:cat,:date,:rec,:notes,:ca)"
                ), {"id": _uid(), "uid": user_id, "type": typ, "label": label, "amount": float(amount),
                    "cat": cat, "date": when, "rec": False, "notes": None, "ca": when})
            except Exception as ex:
                logger.warning("seed finance: %s", ex)
                break
        # Mois précédents (pour la courbe de trésorerie)
        for m in range(1, 4):
            d = (first_of_month - dt.timedelta(days=1)).replace(day=15) - dt.timedelta(days=30 * (m - 1))
            when = dt.datetime(d.year, d.month, 15, 10, 0)
            try:
                await db.execute(text(
                    "INSERT INTO finance_entries (id, user_id, type, label, amount, category, date, recurring, notes, created_at) "
                    "VALUES (:id,:uid,:type,:label,:amount,:cat,:date,:rec,:notes,:ca)"
                ), {"id": _uid(), "uid": user_id, "type": "revenu", "label": "Prestations du mois",
                    "amount": float(6800 + m * 900), "cat": "prestation", "date": when, "rec": False,
                    "notes": None, "ca": when})
                await db.execute(text(
                    "INSERT INTO finance_entries (id, user_id, type, label, amount, category, date, recurring, notes, created_at) "
                    "VALUES (:id,:uid,:type,:label,:amount,:cat,:date,:rec,:notes,:ca)"
                ), {"id": _uid(), "uid": user_id, "type": "depense", "label": "Charges du mois",
                    "amount": float(1400 + m * 120), "cat": "charges", "date": when, "rec": False,
                    "notes": None, "ca": when})
            except Exception as ex:
                logger.warning("seed finance prev: %s", ex)
                break

        # ── 5) Prospects / pipeline (user_leads JSON) ───────────────────────
        leads = [
            ("Julie Bernard", "Nova Agency · Resp. Marketing", "linkedin", 85, "discussing", "En négociation", 3900,
             "Cherche une solution pour automatiser sa prospection, budget validé."),
            ("Lucas Martin", "GreenFood · Fondateur", "site web", 78, "discussing", "Proposition envoyée", 2800,
             "A demandé un devis pour un accompagnement growth 3 mois."),
            ("Sophie Leroy", "Tech & You · Dirigeante", "réseaux sociaux", 65, "contacted", "En contact", 2300,
             "Intéressée après un post LinkedIn, à relancer cette semaine."),
            ("Thomas Dubois", "Alpha Studio · CEO", "linkedin", 45, "detected", "À qualifier", 1750,
             "A liké plusieurs contenus, pas encore contacté."),
            ("Marie Petit", "Impact Club · Consultante", "recommandation", 72, "contacted", "Qualifié", 2600,
             "Recommandée par un client, forte douleur sur l'organisation."),
            ("Paul & Co", "Paul & Co · Directeur associé", "événement", 80, "discussing", "Proposition", 2750,
             "Rencontré en salon, demande une offre équipe."),
            ("Atelier Bloom", "Atelier Bloom · Fondatrice", "site web", 35, "detected", "À qualifier", 1500,
             "Formulaire de contact rempli, besoin à clarifier."),
            ("Julien Lefèvre", "Start Learning · Entrepreneur", "linkedin", 50, "contacted", "En contact", 2300,
             "Échange en cours sur une formation IA."),
            ("Camille Roy", "Studio Nord · Freelance", "forum", 88, "detected", "Douleur forte", 2100,
             "Post « je n'arrive plus à suivre mes leads » — intention très haute."),
            ("Nadia K.", "Boutique Éthique · Gérante", "réseaux sociaux", 61, "detected", "À qualifier", 1650,
             "Commentaire sur un article, curieuse de l'offre."),
            ("Hugo Meyer", "DevShop · CTO", "recommandation", 76, "contacted", "Qualifié", 3200,
             "Besoin d'un cockpit de pilotage pour son activité de conseil."),
            ("Léa Fontaine", "Coach & Sens · Coach", "événement", 69, "contacted", "En contact", 1900,
             "Souhaite structurer son offre et sa prospection."),
            ("Marc Antoine", "Artisan Bois · Artisan", "site web", 42, "detected", "À qualifier", 1200,
             "A téléchargé un guide gratuit."),
            ("Inès B.", "SaaSly · Head of Growth", "linkedin", 91, "discussing", "En négociation", 4200,
             "Décision imminente, compare 2 solutions."),
            ("Olivier P.", "Cabinet OP · Consultant", "forum", 58, "detected", "À qualifier", 1550,
             "Question sur l'automatisation des relances."),
            ("Sarah B.", "Wellness Lab · Fondatrice", "recommandation", 74, "contacted", "Qualifié", 2450,
             "Recommandée, rendez-vous à planifier."),
            ("Kevin D.", "Local Eats · Gérant", "réseaux sociaux", 47, "detected", "À qualifier", 1400,
             "Interaction sur une story, à nurturer."),
            ("Amélie V.", "Studio Créa · Directrice", "événement", 82, "discussing", "Proposition", 3050,
             "Proposition envoyée après un appel très positif."),
        ]
        for name, sub, source, score, stage, intent, value, snippet in leads:
            created = now - dt.timedelta(days=(hash(name) % 25), hours=(hash(source) % 12))
            data = {
                "id": _uid(),
                "name": name, "sub": sub, "source": source, "score": score,
                "stage": stage, "intent": intent, "value": value, "snippet": snippet,
                "campaign": "all",
                "date": created.strftime("%d %b"),
            }
            try:
                await db.execute(text(
                    "INSERT INTO user_leads (id, user_id, data, created_at, updated_at) "
                    "VALUES (:id,:uid,:d,:c,:u)"
                ), {"id": data["id"], "uid": user_id, "d": json.dumps(data, ensure_ascii=False),
                    "c": created, "u": created})
            except Exception as ex:
                logger.warning("seed leads: %s", ex)
                break

        await db.commit()
        logger.info("Demo data seeded for Thomas (%s)", user_id)
    except Exception as ex:
        logger.warning("ensure_thomas_demo failed: %s", ex)
        try:
            await db.rollback()
        except Exception:
            pass
