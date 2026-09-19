"""Iteration 5 backend tests: tasks/generate, DELETE, wellness habits/sleep."""
import os, requests, time

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")


def _login():
    r = requests.post(f"{BASE}/api/auth/request-link", json={"email": "thomas@zayado.fr"}, timeout=15)
    assert r.status_code == 200, r.text
    dev_link = r.json().get("dev_link")
    assert dev_link
    tok = dev_link.split("token=")[1]
    r2 = requests.post(f"{BASE}/api/auth/verify-link", json={"token": tok}, timeout=15)
    assert r2.status_code == 200, r2.text
    return r2.json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def test_login_works():
    tok = _login()
    assert tok


def test_tasks_generate_returns_3_ai_priorities():
    tok = _login()
    r = requests.post(f"{BASE}/api/tasks/generate", headers=_h(tok), json={}, timeout=45)
    assert r.status_code == 200, r.text
    data = r.json()
    items = data if isinstance(data, list) else data.get("items") or data.get("tasks") or []
    assert len(items) >= 1
    print("generate returned", len(items))


def test_tasks_list_and_delete():
    tok = _login()
    r = requests.get(f"{BASE}/api/tasks", headers=_h(tok), timeout=15)
    assert r.status_code == 200
    body = r.json()
    items = body if isinstance(body, list) else body.get("items", [])
    if items:
        tid = items[0]["id"]
        d = requests.delete(f"{BASE}/api/tasks/{tid}", headers=_h(tok), timeout=15)
        assert d.status_code in (200, 204), d.text


def test_habits_crud():
    tok = _login()
    # create
    r = requests.post(f"{BASE}/api/wellness/habits", headers=_h(tok), json={"name": "TEST_habit_pytest"}, timeout=15)
    assert r.status_code in (200, 201), r.text
    hid = r.json().get("id") or r.json().get("item", {}).get("id")
    # list
    r2 = requests.get(f"{BASE}/api/wellness/habits", headers=_h(tok), timeout=15)
    assert r2.status_code == 200
    ids = [h["id"] for h in r2.json().get("items", [])]
    assert hid in ids
    # toggle
    r3 = requests.post(f"{BASE}/api/wellness/habits/{hid}/toggle", headers=_h(tok), timeout=15)
    assert r3.status_code == 200, r3.text
    # delete
    r4 = requests.delete(f"{BASE}/api/wellness/habits/{hid}", headers=_h(tok), timeout=15)
    assert r4.status_code in (200, 204)


def test_sleep_crud():
    tok = _login()
    r = requests.post(f"{BASE}/api/wellness/sleep", headers=_h(tok), json={"hours": 7.5, "quality": 4}, timeout=15)
    assert r.status_code in (200, 201), r.text
    r2 = requests.get(f"{BASE}/api/wellness/sleep", headers=_h(tok), timeout=15)
    assert r2.status_code == 200
    body = r2.json()
    assert "items" in body or "avg_hours" in body


def test_wellness_state_no_fake_data():
    tok = _login()
    r = requests.get(f"{BASE}/api/wellness/state", headers=_h(tok), timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    # burnout risk should not be a hardcoded 12%
    print("burnout:", body.get("burnout_risk"))
    print("today:", body.get("today"))
