import sys
import os
import time
import json
import argparse
import logging
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.backend.models import MessageStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("BackendServer")

class MessagingRequestHandler(BaseHTTPRequestHandler):
    server_version = "DistributedMessaging/1.0"

    def log_message(self, format, *args):
        logger.debug(f"{self.address_string()} - {format % args}")

    def _send_json_response(self, status_code: int, data: Dict[str, Any], start_time: float):
        payload = json.dumps(data).encode("utf-8")
        duration_ms = (time.time() - start_time) * 1000.0
        
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Backend-Server", self.server.server_id)
        self.send_header("X-Backend-Host", self.server.host)
        self.send_header("X-Backend-Port", str(self.server.port))
        self.send_header("X-Handled-By", f"{self.server.server_id}:{self.server.port}")
        self.send_header("X-Response-Time-Ms", f"{duration_ms:.2f}")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        
        self.wfile.write(payload)
        self.server.request_count += 1
        
        logger.info(
            f"[{self.server.server_id}] {self.command} {self.path} -> {status_code} "
            f"(took {duration_ms:.2f}ms, total requests: {self.server.request_count})"
        )

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        start_time = time.time()
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        if path in ["/health", "/api/status", "/api/health"]:
            uptime = time.time() - self.server.start_time
            response = {
                "status": "healthy",
                "service": "messaging-backend",
                "server_id": self.server.server_id,
                "host": self.server.host,
                "port": self.server.port,
                "uptime_seconds": round(uptime, 2),
                "total_requests": self.server.request_count,
                "message_count": self.server.store.count(),
                "timestamp": time.time()
            }
            self._send_json_response(200, response, start_time)
            return

        if path == "/api/channels":
            channels = self.server.store.get_channels()
            response = {
                "server_id": self.server.server_id,
                "channels": channels,
                "count": len(channels)
            }
            self._send_json_response(200, response, start_time)
            return

        if path == "/api/messages":
            channel = query.get("channel", [None])[0]
            limit_str = query.get("limit", ["50"])[0]
            try:
                limit = int(limit_str)
            except ValueError:
                limit = 50
            messages = self.server.store.get_messages(channel=channel, limit=limit)
            response = {
                "server_id": self.server.server_id,
                "channel": channel,
                "messages": messages,
                "count": len(messages)
            }
            self._send_json_response(200, response, start_time)
            return

        if path.startswith("/api/messages/"):
            parts = path.strip("/").split("/")
            if len(parts) == 3 and parts[2].isdigit():
                msg_id = int(parts[2])
                msg = self.server.store.get_message_by_id(msg_id)
                if msg:
                    response = {
                        "server_id": self.server.server_id,
                        "message": msg
                    }
                    self._send_json_response(200, response, start_time)
                else:
                    self._send_json_response(404, {"error": "Message not found", "id": msg_id}, start_time)
                return

        if path == "/api/workload":
            delay_ms = float(query.get("delay_ms", [str(self.server.default_delay_ms)])[0])
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            
            response = {
                "server_id": self.server.server_id,
                "status": "completed",
                "simulated_delay_ms": delay_ms,
                "timestamp": time.time()
            }
            self._send_json_response(200, response, start_time)
            return

        if path == "/":
            response = {
                "name": "Distributed Messaging Backend Service",
                "server_id": self.server.server_id,
                "endpoints": [
                    "GET /health",
                    "GET /api/status",
                    "GET /api/channels",
                    "GET /api/messages",
                    "POST /api/messages",
                    "GET /api/messages/{id}",
                    "GET/POST /api/workload"
                ]
            }
            self._send_json_response(200, response, start_time)
            return

        self._send_json_response(404, {"error": "Endpoint not found", "path": path}, start_time)

    def do_POST(self):
        start_time = time.time()
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = {}
        if content_length > 0:
            try:
                raw_body = self.rfile.read(content_length).decode("utf-8")
                body = json.loads(raw_body)
            except Exception as e:
                self._send_json_response(400, {"error": f"Invalid JSON payload: {str(e)}"}, start_time)
                return

        if path == "/api/messages":
            sender = body.get("sender", "Anonymous")
            content = body.get("content", "")
            channel = body.get("channel", "general")

            if not content.strip():
                self._send_json_response(400, {"error": "Message content cannot be empty"}, start_time)
                return

            new_msg = self.server.store.add_message(sender=sender, content=content, channel=channel)
            response = {
                "server_id": self.server.server_id,
                "message": "Message created successfully",
                "data": new_msg
            }
            self._send_json_response(201, response, start_time)
            return

        if path == "/api/workload":
            delay_ms = float(body.get("delay_ms", self.server.default_delay_ms))
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            
            response = {
                "server_id": self.server.server_id,
                "status": "completed",
                "simulated_delay_ms": delay_ms,
                "body_echo": body.get("payload", None),
                "timestamp": time.time()
            }
            self._send_json_response(200, response, start_time)
            return

        self._send_json_response(404, {"error": "Endpoint not found", "path": path}, start_time)


class BackendHTTPServer(ThreadingHTTPServer):
    def __init__(self, host: str, port: int, server_id: str, default_delay_ms: float = 0.0):
        self.host = host
        self.port = port
        self.server_id = server_id
        self.default_delay_ms = default_delay_ms
        self.start_time = time.time()
        self.request_count = 0
        self.store = MessageStore()
        super().__init__((host, port), MessagingRequestHandler)


def run_backend(host: str = "0.0.0.0", port: int = 8001, server_id: str = "Sys2", default_delay_ms: float = 0.0):
    server = BackendHTTPServer(host, port, server_id, default_delay_ms)
    logger.info(f"Messaging Backend [{server_id}] starting on http://{host}:{port}")
    logger.info(f"Health check: http://{host}:{port}/health")
    logger.info(f"Messages API: http://{host}:{port}/api/messages")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info(f"Shutting down backend [{server_id}]...")
    finally:
        server.server_close()
        logger.info(f"Backend [{server_id}] stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed Messaging Backend Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind (default: 8001)")
    parser.add_argument("--id", type=str, default="Sys2", help="Server ID (e.g. Sys2, Sys3, Sys4)")
    parser.add_argument("--delay-ms", type=float, default=0.0, help="Default simulated processing delay in ms")
    
    args = parser.parse_args()
    run_backend(host=args.host, port=args.port, server_id=args.id, default_delay_ms=args.delay_ms)
