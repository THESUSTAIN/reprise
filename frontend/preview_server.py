from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BUILD_DIR = Path(__file__).resolve().parent / "build"
BACKEND_URL = "http://127.0.0.1:8001"


class SpaHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        requested = urlparse(path).path.lstrip("/")
        return str(BUILD_DIR / requested)

    def _proxy_api(self):
        body = None
        if self.command in {"POST", "PUT", "PATCH"}:
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        request = Request(
            f"{BACKEND_URL}{self.path}",
            data=body,
            method=self.command,
            headers={k: v for k, v in self.headers.items() if k.lower() not in {"host", "content-length"}},
        )
        try:
            with urlopen(request, timeout=45) as response:
                payload = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() not in {"transfer-encoding", "connection"}:
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(payload)
        except HTTPError as error:
            self.send_response(error.code)
            self.send_header("Content-Type", error.headers.get("Content-Type", "application/json"))
            self.end_headers()
            self.wfile.write(error.read())

    def do_GET(self):
        if urlparse(self.path).path.startswith("/api/"):
            return self._proxy_api()
        requested = Path(self.translate_path(self.path))
        if requested.exists() and requested.is_file():
            return super().do_GET()
        self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path.startswith("/api/"):
            return self._proxy_api()
        self.send_error(404)

    do_PUT = do_POST
    do_PATCH = do_POST
    do_DELETE = do_POST


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 3001), SpaHandler)
    print("Prévisualisation Cours-main disponible sur le port 3001", flush=True)
    server.serve_forever()
