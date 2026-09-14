from routes.server import app

for index, route in enumerate(app.routes):
    print(index, type(route).__name__, getattr(route, "path", None), getattr(route, "name", None), repr(route)[:220])
print("openapi_paths", len(app.openapi().get("paths", {})))
for path in sorted(app.openapi().get("paths", {})):
    if any(key in path for key in ("growth", "vision", "connections", "pilotage", "prefs")):
        print("openapi", path)
