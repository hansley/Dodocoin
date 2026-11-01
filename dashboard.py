"""Local-only HTTP dashboard for DodoCoin's educational four-shard ledger."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import json
import threading

from dodocoin import ShardedLedger, shard_for
from algorithm_lab import run_benchmark

HOST = "127.0.0.1"
PORT = 8765
ledger = ShardedLedger()
operation_lock = threading.RLock()
events = []
benchmark_result = None
benchmark_lock = threading.Lock()

def record(kind, detail):
    events.append({"id": len(events) + 1, "type": kind, "detail": detail})
    del events[:-100]

def seed():
    for name, coins in [("alice", "150"), ("bob", "75"), ("charlie", "220"),
                        ("diana", "100"), ("eve", "90"), ("frank", "60"),
                        ("grace", "130"), ("heidi", "180")]:
        ledger.create_account(name, coins)
    record("system", "Eight sample accounts created")

class Handler(BaseHTTPRequestHandler):
    def _json(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            data = (Path(__file__).resolve().parent / "dashboard.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; base-uri 'none'; object-src 'none'")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif path == "/api/state":
            with operation_lock:
                self._json(200, {"ledger": ledger.snapshot(), "events": list(reversed(events))})
        elif path == "/api/benchmark":
            with benchmark_lock:
                self._json(200, {"result": benchmark_result})
        elif path == "/dashboard.js":
            data = (Path(__file__).resolve().parent / "dashboard.js").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in ("/api/accounts", "/api/transfers", "/api/settle", "/api/benchmark"):
            return self._json(404, {"error": "Not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 2 or length > 4096:
                raise ValueError("Invalid request size")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object")
            if path == "/api/benchmark":
                # Run against a separate ledger, never the dashboard account balances.
                if payload != {"category": "sharding", "algorithm": "sha", "transactions": 10000,
                               "cross_percent": 25, "seed": 20261101, "fault": "none"}:
                    raise ValueError("Only the fixed 10,000-transaction SHA benchmark is supported")
                if not benchmark_lock.acquire(blocking=False):
                    return self._json(409, {"error": "Benchmark already running"})
                try:
                    global benchmark_result
                    benchmark_result = run_benchmark(10000, 25, 20261101)
                    return self._json(200, {"result": benchmark_result})
                finally:
                    benchmark_lock.release()
            with operation_lock:
                if path == "/api/accounts":
                    name = payload["name"]
                    if not isinstance(name, str) or len(name) > 64:
                        raise ValueError("Account name must be 1–64 characters")
                    shard = ledger.create_account(name, payload.get("balance", "0"))
                    record("account", f"Created {name} on shard {shard}")
                    result = {"shard": shard}
                elif path == "/api/transfers":
                    sender, recipient = payload["sender"], payload["recipient"]
                    if not isinstance(sender, str) or not isinstance(recipient, str):
                        raise ValueError("Invalid account name")
                    receipt = ledger.transfer(sender, recipient, payload["amount"])
                    record("transfer", f"{sender} sent {payload['amount']} DDC to {recipient}" +
                           (f" (receipt #{receipt.id} pending)" if receipt else " (same shard)"))
                    result = {"receipt_id": receipt.id if receipt else None}
                else:
                    receipt_id = payload["receipt_id"]
                    if type(receipt_id) is not int:
                        raise ValueError("Receipt ID must be an integer")
                    processed = ledger.process_receipt(receipt_id)
                    if processed:
                        record("settlement", f"Settled receipt #{receipt_id}")
                    result = {"processed": processed}
                self._json(200, result)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})

if __name__ == "__main__":
    seed()
    print(f"DodoCoin dashboard: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
