import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.web_api import analyze_raw_payload


UI_PATH = Path(__file__).resolve().parent / "ui" / "simple_test_panel.html"


class StrategyRequestHandler(BaseHTTPRequestHandler):
    server_version = "PokerLBSLite/0.1"

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._send_bytes(
                status=200,
                body=UI_PATH.read_bytes(),
                content_type="text/html; charset=utf-8",
            )
            return

        self._send_json(status=404, payload={"ok": False, "error": "NOT_FOUND"})

    def do_POST(self) -> None:
        if self.path != "/api/analyze":
            self._send_json(status=404, payload={"ok": False, "error": "NOT_FOUND"})
            return

        try:
            payload = self._read_json_body()
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            self._send_json(status=400, payload={"ok": False, "error": "INVALID_JSON"})
            return

        try:
            response = analyze_raw_payload(payload)
        except Exception:
            self._send_json(status=500, payload={"ok": False, "error": "INTERNAL_ERROR"})
            return

        status = 200 if response.get("ok") else 400
        self._send_json(status=status, payload=response)

    def _read_json_body(self) -> object:
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length).decode("utf-8")
        return json.loads(body)

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status=status, body=body, content_type="application/json")

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def create_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), StrategyRequestHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local LBS-Lite test panel.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = create_server(args.host, args.port)
    host, port = server.server_address
    print(f"Serving Poker LBS-Lite Test Panel at http://{host}:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
