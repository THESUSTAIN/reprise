from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_required_lots789_routes_are_in_openapi():
    from routes.server import app

    paths = set(app.openapi().get("paths", {}))
    required = {
        "/api/growth/copilote",
        "/api/vision/brain/panel",
        "/api/vision/brain/connections",
        "/api/connections",
        "/api/connections/providers",
        "/api/pilotage/overview",
        "/api/pilotage/simulate",
        "/api/prefs",
    }
    assert required.issubset(paths), sorted(required - paths)


def test_controlled_ui_has_no_automatic_external_send_in_new_lots():
    root = Path(__file__).resolve().parents[2]
    growth = (root / "frontend/src/pages/Croissance.jsx").read_text()
    pilotage = (root / "frontend/src/pages/Pilotage.jsx").read_text()
    assert "sendEngagement" not in growth + pilotage
    assert "push-crm" not in growth + pilotage
    assert "Aucun message" in growth
