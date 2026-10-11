"""
# Ontology: app.telemetry.server
"""
# Standard Libraries
import os
import json
import socket
import select
import threading
import queue
from pathlib import Path
from typing import Dict, Any, Optional

SOCKET_PATH = "/tmp/ontology.sock"

class TelemetryRequest:
    __slots__ = ("id", "query", "params", "response", "done")

    def __init__(self, req_id: int, query: str, params: Dict[str, Any]):
        self.id = req_id
        self.query = query
        self.params = params
        self.response: Optional[Dict[str, Any]] = None
        self.done = threading.Event()


class TelemetryServer:
    def __init__(self, socket_path: str = SOCKET_PATH):
        self.socket_path = socket_path
        self.inbound_queue: queue.SimpleQueue[TelemetryRequest] = queue.SimpleQueue()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._counter = 0

    def start(self) -> None:
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="TelemetryServer")
        self._thread.start()

    def stop(self) -> None:
        self.running = False
        if self._thread:
            self._thread.join(timeout=0.2)
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

    def _run(self) -> None:
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.socket_path)
        server.listen(4)
        server.setblocking(False)

        while self.running:
            readable, _, _ = select.select([server], [], [], 0.05)
            if not readable:
                continue

            client, _ = server.accept()
            client.settimeout(0.5)
            try:
                raw_data = client.recv(4096)
                if not raw_data:
                    client.close()
                    continue

                payload = json.loads(raw_data.decode("utf-8"))
                self._counter += 1
                req = TelemetryRequest(
                    req_id=self._counter,
                    query=payload.get("query", "assets"),
                    params=payload.get("params", {})
                )

                self.inbound_queue.put(req)

                # Wait up to 50ms (3 ticks at 60Hz) for engine tick resolution
                if req.done.wait(timeout=0.050):
                    response_bytes = json.dumps(req.response).encode("utf-8") + b"\n"
                    client.sendall(response_bytes)
                else:
                    client.sendall(b'{"error": "tick_timeout"}\n')
            except (json.JSONDecodeError, OSError):
                pass
            finally:
                client.close()

        server.close()