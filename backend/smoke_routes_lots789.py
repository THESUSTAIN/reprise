from routes.server import app

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
paths = set(app.openapi().get("paths", {}))
missing = sorted(required - paths)
print(f"routes_total={len(paths)}")
print("missing=" + (",".join(missing) if missing else "none"))
if missing:
    raise SystemExit(1)
print("required_routes=ok")
