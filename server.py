"""
HTTP server for the IRGen Student Learning Portal.

Serves the front-end learning environment and provides JSON REST API endpoints
for compiling, optimizing, simulating, and inspecting IRGen code.
Zero external dependencies (uses standard library http.server).
"""

import http.server
import json
import mimetypes
import os
import socketserver
import sys
import urllib.parse

from irgen.service import compile_pipeline, get_curriculum_examples

# Base directory for static web files
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


class IRGenRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler for IRGen web portal and compilation API."""

    def __init__(self, *args, **kwargs):
        """Initialize handler with web assets directory as root."""
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        """Inject CORS and caching headers."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        """Handle CORS pre-flight checks."""
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        """Handle GET requests for static assets and API endpoints."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/health":
            self._send_json({"status": "ok", "engine": "IRGen", "version": "4.0", "for_loop_supported": True})
            return

        if path == "/api/examples":
            examples = get_curriculum_examples()
            self._send_json({"examples": examples})
            return

        # Redirect root to index.html
        if path == "/" or path == "":
            self.path = "/index.html"

        return super().do_GET()

    def do_POST(self):
        """Handle POST requests for compilation and execution."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/compile":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                payload = json.loads(body) if body else {}

                source_code = payload.get("code", "")
                initial_env = payload.get("env", {})

                # Ensure initial_env has integer values
                cleaned_env = {}
                for k, v in initial_env.items():
                    try:
                        cleaned_env[str(k).strip()] = int(v)
                    except (ValueError, TypeError):
                        pass

                compilation_result = compile_pipeline(source_code, cleaned_env)
                self._send_json(compilation_result)

            except Exception as e:
                self._send_json({
                    "success": False,
                    "stage": "Server",
                    "error": f"Internal server error: {e}",
                }, status=500)
            return

        self._send_json({"error": "Endpoint not found"}, status=404)

    def _send_json(self, data, status=200):
        """Helper to send a JSON HTTP response."""
        encoded = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format_str, *args):
        """Clean terminal logging."""
        sys.stderr.write(f"[IRGen Server] {self.address_string()} - {format_str % args}\n")


def run_server(port=8000, host="127.0.0.1"):
    """
    Start the IRGen portal HTTP server.

    Args:
        port (int): Port number to bind to (default: 8000).
        host (str): Interface to bind to (default: 127.0.0.1).
    """
    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True

    try:
        with ThreadedTCPServer((host, port), IRGenRequestHandler) as httpd:
            print("=" * 60)
            print(f"  IRGen Student Learning Portal Backend Running")
            print(f"  Access Portal at:  http://{host}:{port}/")
            print(f"  API Endpoint:      http://{host}:{port}/api/compile")
            print(f"  Press Ctrl+C to stop the server")
            print("=" * 60)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[IRGen Server] Shutting down server gracefully...")
    except OSError as e:
        print(f"\n[IRGen Server] Error starting server on port {port}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port=port)
