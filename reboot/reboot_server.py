"""
Standalone reboot microservice for Meduseld.
Runs independently of the main Flask app so it can reboot the server
even when the panel is down.

Listens on port 5002, accepts POST /reboot with a shared secret token.
Runs as its own systemd service: meduseld-reboot.service
"""

import json
import os
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 5002
REBOOT_SECRET = os.environ.get("REBOOT_SECRET")


class RebootHandler(BaseHTTPRequestHandler):
    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/reboot":
            self.send_response(404)
            self.end_headers()
            return

        if not REBOOT_SECRET:
            self._respond(503, {"error": "Reboot secret not configured"})
            return

        # Read request body
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
            return

        token = data.get("token", "")
        if token != REBOOT_SECRET:
            print(f"[WARN] Unauthorized reboot attempt from {self.client_address[0]}")
            self._respond(403, {"error": "Unauthorized"})
            return

        print(f"[CRITICAL] SYSTEM REBOOT initiated from {self.client_address[0]}")
        self._respond(200, {"success": True, "message": "System reboot initiated"})

        # Reboot after a short delay so the response can be sent
        def do_reboot():
            import time
            time.sleep(2)
            subprocess.call(["sudo", "reboot"])

        threading.Thread(target=do_reboot, daemon=True).start()

    def _respond(self, code, data):
        self.send_response(code)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        print(f"[reboot-service] {args[0]}")


if __name__ == "__main__":
    if not REBOOT_SECRET:
        print("[ERROR] REBOOT_SECRET environment variable is not set. Exiting.")
        exit(1)

    server = HTTPServer(("0.0.0.0", PORT), RebootHandler)
    print(f"[reboot-service] Listening on 0.0.0.0:{PORT}")
    server.serve_forever()
