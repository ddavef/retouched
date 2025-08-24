"""
retouched
Copyright (C) 2025 ddavef/KinteLiX

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import http.server
import socketserver
import urllib.parse
import json
import threading
from typing import Dict
from error_handler import ErrorHandler

# This HTTP server is needed for Touchy to connect to the game
class BMRegistryHTTPHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.error_handler = ErrorHandler()
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        self.error_handler.log_info(f"[HTTP] GET request: {self.path}", "HTTP_SERVER")
        self.error_handler.log_info(f"[HTTP] Query params: {query_params}", "HTTP_SERVER")

        if parsed_url.path == '/bmregistry/getInfo.jsp':
            self.handle_get_info(query_params)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/bmregistry/metrics':
            self.handle_metrics()
        else:
            self.send_error(404, "Not Found")

    def handle_metrics(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        form = urllib.parse.parse_qs(post_data)

        action = form.get('action', [''])[0]
        events = form.get('events', [''])[0]
        token = form.get('token', [''])[0]

        self.error_handler.log_info(f"[HTTP] Metrics POST: action={action}, events={events}, token={token}", "HTTP_SERVER")

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'{"status":"success"}')

    def handle_get_info(self, query_params: Dict[str, list]):
        app_id = query_params.get('appId', [None])[0]
        device_id = query_params.get('deviceId', [None])[0]

        if not app_id or not device_id:
            self.send_error(400, "Missing required parameters: appId and deviceId")
            return

        response_data = {
            "appId": app_id,
            "deviceId": device_id,
            "play": 0,
            "purchase": 0,
            "premium": False, # It's always free! :)
            "trial": False,
            "canPlay": True,
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def log_message(self, form, *args):
        self.error_handler.log_info(f"[HTTP] {form % args}", "HTTP_SERVER")

class BMRegistryHTTPServer:
    def __init__(self, host: str = '', port: int = 8080):
        self.host = host
        self.port = port
        self.httpd = None
        self.server_thread = None
        self.running = False
        self.error_handler = ErrorHandler()

    def start(self):
        try:
            def handler_factory(*args, **kwargs):
                return BMRegistryHTTPHandler(*args, **kwargs)

            self.httpd = socketserver.TCPServer((self.host, self.port), handler_factory)
            self.httpd.allow_reuse_address = True

            self.error_handler.log_info(f"[HTTP] HTTP Server starting on {self.host or '0.0.0.0'}:{self.port}", "HTTP_SERVER")

            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.running = True
            self.server_thread.start()

            self.error_handler.log_info(f"[HTTP] Registry info endpoint: http://localhost:{self.port}/bmregistry/getInfo.jsp", "HTTP_SERVER")

        except Exception as e:
            print(f"Failed to start HTTP server: {e}")
            self.running = False

    def _run_server(self):
        try:
            self.httpd.serve_forever()
        except Exception as e:
            print(f"HTTP Server error: {e}")
        finally:
            self.running = False

    def stop(self):
        if self.httpd and self.running:
            self.error_handler.log_info("[HTTP] Shutting down HTTP server...", "HTTP_SERVER")
            self.httpd.shutdown()
            self.httpd.server_close()
            self.running = False

            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=5)

            self.error_handler.log_info("[HTTP] HTTP server stopped", "HTTP_SERVER")

    def is_running(self) -> bool:
        return self.running

if __name__ == "__main__":
    http_server = BMRegistryHTTPServer(host='', port=8080)
    http_server.start()

    try:
        import time
        while http_server.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        http_server.stop()