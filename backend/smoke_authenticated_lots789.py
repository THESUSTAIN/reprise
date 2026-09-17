import asyncio
import os
from pathlib import Path

os.environ["CAP_VIVANT_LOCAL_DB"] = "1"
os.environ["JWT_SECRET"] = "smoke-test-secret-32-characters-long"
os.environ["DEMO_LOGIN_EMAILS"] = "thomas@zayado.fr"

from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from database import Base, engine, async_session
from models import User
from routes.server import app

EMAIL = "thomas@zayado.fr"


async def main():
    db_path = Path(__file__).with_name("zayado.db")
    if db_path.exists():
        db_path.unlink()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as db:
        db.add(User(email=EMAIL, name="Thomas Test", password_hash="not-used", role="admin"))
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post("/api/auth/demo-login", json={"email": EMAIL})
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        before = await client.get("/api/prefs", headers=headers)
        assert before.status_code == 200, before.text
        marker = "lots789-persistence-check"
        saved = await client.put("/api/prefs", headers=headers, json={"vision_memory": {"marker": marker}})
        assert saved.status_code == 200, saved.text
        after = await client.get("/api/prefs", headers=headers)
        assert after.status_code == 200, after.text
        assert after.json().get("vision_memory", {}).get("marker") == marker, after.text

        task = await client.post("/api/tasks", headers=headers, json={"label": "Tâche de recette lots 789", "priority": "high", "notes": "Contrôle persistance"})
        assert task.status_code == 200, task.text
        task_list = await client.get("/api/tasks", headers=headers)
        assert task_list.status_code == 200, task_list.text
        assert any(item.get("label") == "Tâche de recette lots 789" for item in task_list.json().get("items", []))

        lead = await client.post("/api/growth/leads", headers=headers, json={"name": "Prospect de recette", "company": "Zayado Test", "snippet": "Besoin explicite de qualification commerciale", "source": "recette"})
        assert lead.status_code == 200, lead.text
        lead_id = lead.json()["lead"]["id"]
        qualify_guard = await client.post(f"/api/growth/leads/{lead_id}/qualify", headers=headers, json={"notes": "Test"})
        assert qualify_guard.status_code == 403, qualify_guard.text
        task_guard = await client.post("/api/tasks/generate", headers=headers)
        assert task_guard.status_code == 403, task_guard.text
        document_guard = await client.post("/api/documents/generate", headers=headers, json={"name": "Test", "type": "note", "prompt": "Test"})
        assert document_guard.status_code == 403, document_guard.text
        lead_list = await client.get("/api/growth", headers=headers)
        assert lead_list.status_code == 200, lead_list.text
        lead_payload = lead_list.json()
        persisted_leads = [item for items in lead_payload.get("leads_by_campaign", {}).values() for item in items]
        assert any(item.get("name") == "Prospect de recette" for item in persisted_leads), lead_payload
        pipeline = await client.get("/api/growth/pipeline", headers=headers)
        assert pipeline.status_code == 200, pipeline.text
        assert any(item.get("leads") for item in pipeline.json().get("stages", []))

        simulation = await client.post("/api/pilotage/simulate", headers=headers, json={"nb_contrats": 2, "montant_moyen": 1000, "depenses_supplementaires": 200})
        assert simulation.status_code == 200, simulation.text
        assert simulation.json()["projected_revenue"] == 2000
        assert simulation.json()["persisted"] is False
        saved_history = await client.post("/api/pilotage/simulations", headers=headers, json={"label": "Recette complète", "scenarios": [{"id": "central", "result": simulation.json()}]})
        assert saved_history.status_code == 200, saved_history.text
        simulation_history = await client.get("/api/pilotage/simulations", headers=headers)
        assert simulation_history.status_code == 200, simulation_history.text
        assert simulation_history.json()["items"][0]["label"] == "Recette complète"

        document = await client.post("/api/documents", headers=headers, json={"name": "Note de recette", "type": "general", "content": "Repère persistant pour le second cerveau", "source": "humain"})
        assert document.status_code == 200, document.text
        documents = await client.get("/api/documents", headers=headers)
        assert documents.status_code == 200, documents.text
        assert any(item.get("name") == "Note de recette" for item in documents.json().get("items", []))

        permissions = await client.put("/api/prefs", headers=headers, json={"ai_permissions": {"prepare_task": True}})
        assert permissions.status_code == 200, permissions.text
        stored_permissions = await client.get("/api/prefs", headers=headers)
        assert stored_permissions.json().get("ai_permissions", {}).get("prepare_task") is True

    print("authenticated_demo_login=ok")
    print("prefs_persistence=ok")
    print("task_persistence=ok")
    print("lead_persistence=ok")
    print("pilotage_simulation=ok")
    print("simulation_history=ok")
    print("second_brain_documents=ok")
    print("ai_permissions=ok")
    print("server_permission_guards=ok")


if __name__ == "__main__":
    asyncio.run(main())
