"""Iteration 3: Backend sanity for Croissance + Vision Board + Simulation (thomas account)."""
import os
import requests
import pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-panel-416.preview.emergentagent.com").rstrip("/")
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYjA4M2I1Ny1jYTU3LTQzMDUtYWM5YS1lMGU1OGYyYTFhMmEiLCJqdGkiOiI4MDE3ZjEwOS1lODc1LTRiMDEtYjVmMS0zNjM2NDUwZTc4MTIiLCJleHAiOjE3ODYwNDM4NzAsImlhdCI6MTc4NTQzOTA3MH0.E2s3pROh4NBFffewELH1vnfui1UV0nBOUiaQjEOVl-c"
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def test_auth_me():
    r = requests.get(f"{BASE}/api/auth/me", headers=H, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "email" in data or "id" in data


def test_growth_all():
    r = requests.get(f"{BASE}/api/growth", headers=H, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    # Must contain at least a few expected keys
    keys = set(data.keys())
    assert "dashboard" in keys or "campaigns" in keys or "leads" in keys, f"Missing expected growth keys: {keys}"


def test_vision_board():
    r = requests.get(f"{BASE}/api/vision/board", headers=H, timeout=15)
    assert r.status_code == 200, r.text


def test_vision_canvas():
    r = requests.get(f"{BASE}/api/vision/board/canvas", headers=H, timeout=15)
    assert r.status_code == 200, r.text


def test_vision_live_data():
    r = requests.get(f"{BASE}/api/vision/board/live-data", headers=H, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    cards = data.get("cards") or data
    # Expect 3 cards with keys ca, wellness, prospects
    if isinstance(cards, list):
        assert len(cards) >= 3
    else:
        assert isinstance(data, dict)


def test_simulation_state():
    r = requests.get(f"{BASE}/api/simulation/state", headers=H, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("started") is True, f"Expected started=True: {data}"
    clients = data.get("clients") or []
    assert len(clients) >= 3, f"Expected >=3 clients: got {len(clients)}"


def test_simulation_submit_task():
    """Submit an answer to the first available task and verify Mammouth feedback fields."""
    state = requests.get(f"{BASE}/api/simulation/state", headers=H, timeout=15).json()
    clients = state.get("clients", [])
    assert clients, "No clients in simulation state"
    client_id = clients[0]["id"]
    # Get / create task for that client
    r_task = requests.get(f"{BASE}/api/simulation/clients/{client_id}/task", headers=H, timeout=30)
    assert r_task.status_code == 200, f"get task: {r_task.status_code} {r_task.text[:400]}"
    task = r_task.json()
    task_id = task.get("id")
    assert task_id, f"Task has no id: {task}"

    payload = {"response_text": "Pour cette mission d'expertise comptable, je propose d'analyser en profondeur les états financiers du client sur les 3 derniers exercices, avec un focus sur les ratios de liquidité (current ratio, quick ratio), les ratios d'endettement (gearing, DSCR), et la marge d'EBITDA. Je recommanderai ensuite une restructuration éventuelle de la dette et un plan de trésorerie prévisionnel sur 12 mois glissants."}
    r = requests.post(f"{BASE}/api/simulation/tasks/{task_id}/submit", headers=H, json=payload, timeout=90)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:500]}"
    data = r.json()
    feedback = data
    for k in ("score", "what_went_well", "improvements_needed", "learning_point", "client_reaction"):
        assert k in feedback, f"Missing feedback field '{k}' in response: {list(feedback.keys())}"
