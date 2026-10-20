from __future__ import annotations

import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List
from urllib.parse import urlparse


class Hub:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.subscribers: List[queue.Queue] = []
        self.history: List[Dict[str, Any]] = []
        self.status = "idle"
        self.clients = 0

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=200)
        with self.lock:
            self.subscribers.append(q)
            self.clients = len(self.subscribers)
            for item in self.history[-30:]:
                try:
                    q.put_nowait(item)
                except queue.Full:
                    break
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self.lock:
            if q in self.subscribers:
                self.subscribers.remove(q)
            self.clients = len(self.subscribers)

    def publish(self, event: str, data: Dict[str, Any] | None = None) -> None:
        msg = {"event": event, "data": data or {}, "ts": time.time()}
        with self.lock:
            self.history.append(msg)
            if len(self.history) > 100:
                self.history = self.history[-100:]
            dead = []
            for sub in self.subscribers:
                try:
                    sub.put_nowait(msg)
                except queue.Full:
                    dead.append(sub)
            for sub in dead:
                if sub in self.subscribers:
                    self.subscribers.remove(sub)
            self.clients = len(self.subscribers)


HUB = Hub()

INJECT_JS = r"""
(function () {
  if (window.__typebotLive) return;
  window.__typebotLive = true;
  const PORT = __PORT__;
  const BASE = "http://127.0.0.1:" + PORT;
  const box = document.createElement("div");
  box.id = "typebot-live";
  box.style.cssText = ["position:fixed","top:14px","right:14px","z-index:2147483647","min-width:220px","max-width:360px","background:#0d0d0d","color:#ff1a1a","font-family:'Courier New',Courier,monospace","font-size:14px","line-height:1.35","padding:12px 16px","border:2px solid #ff1a1a","border-radius:8px","box-shadow:0 0 18px rgba(255,0,0,0.45)","pointer-events:none","user-select:none"].join(";");
  box.innerHTML = '<div style="font-weight:700;font-size:16px;color:#ff1a1a;">TypeBot</div><div style="font-size:11px;color:#b0b0b0;margin:2px 0 8px;">By DarkFox · LIVE</div><div id="typebot-status" style="font-size:11px;color:#888;margin-bottom:6px;">connecting…</div><div id="typebot-text" style="color:#fff;font-size:13px;min-height:1.2em;white-space:pre-wrap;word-break:break-word;"></div>';
  (document.documentElement || document.body).appendChild(box);
  const statusEl = document.getElementById("typebot-status");
  const textEl = document.getElementById("typebot-text");
  let full = "";
  function setStatus(s, ok) { statusEl.textContent = s; statusEl.style.color = ok ? "#4caf50" : "#ff9800"; }
  function apply(msg) {
    const e = msg.event; const d = msg.data || {};
    if (e === "status") setStatus(d.text || "live", true);
    if (e === "clear") { full = ""; textEl.textContent = ""; }
    if (e === "char") { full += (d.ch || ""); textEl.textContent = full; }
    if (e === "text") { full = d.text || ""; textEl.textContent = full; }
    if (e === "line") { full += (d.text || "") + "\n"; textEl.textContent = full; }
  }
  function connect() {
    const es = new EventSource(BASE + "/events");
    es.onopen = function () {
      setStatus("connected · live", true);
      fetch(BASE + "/hello", { method: "POST", body: JSON.stringify({ href: location.href }) }).catch(function(){});
    };
    es.onmessage = function (ev) { try { apply(JSON.parse(ev.data)); } catch (err) {} };
    es.onerror = function () { setStatus("reconnecting…", false); es.close(); setTimeout(connect, 1500); };
  }
  connect();
  console.log("%c[TypeBot] LIVE connected to Python on :" + PORT, "color:#ff1a1a;font-weight:bold");
})();
"""

DEMO_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>TypeBot LIVE · weHateTP</title>
<style>body{margin:0;background:#111;color:#eee;font-family:system-ui,sans-serif}main{max-width:640px;margin:40px auto;padding:24px}h1{color:#ff1a1a;font-family:'Courier New',monospace}p{color:#aaa}code{background:#222;padding:2px 6px;border-radius:4px}</style>
</head><body><main><h1>TypeBot LIVE</h1><p>Connected to <code>weHateTP</code>. Overlay is top-right.</p><p>Type in the Python terminal – text appears here live.</p></main>
<script src="/inject.js"></script></body></html>"""


def make_handler(port: int):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_GET(self):
            path = urlparse(self.path).path
            if path in ("/", "/demo"):
                body = DEMO_HTML.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._cors()
                self.end_headers()
                self.wfile.write(body)
                return
            if path == "/inject.js":
                js = INJECT_JS.replace("__PORT__", str(port)).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.send_header("Content-Length", str(len(js)))
                self._cors()
                self.end_headers()
                self.wfile.write(js)
                return
            if path == "/status":
                data = json.dumps({"status": HUB.status, "clients": HUB.clients}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self._cors()
                self.end_headers()
                self.wfile.write(data)
                return
            if path == "/events":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self._cors()
                self.end_headers()
                q = HUB.subscribe()
                try:
                    self.wfile.write(b": ok\n\n")
                    self.wfile.flush()
                    while True:
                        try:
                            msg = q.get(timeout=15)
                            self.wfile.write(f"data: {json.dumps(msg)}\n\n".encode())
                            self.wfile.flush()
                        except queue.Empty:
                            self.wfile.write(b": ping\n\n")
                            self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass
                finally:
                    HUB.unsubscribe(q)
                return
            self.send_error(404)

        def do_POST(self):
            path = urlparse(self.path).path
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                payload = {}
            if path == "/hello":
                HUB.publish("status", {"text": f"page: {payload.get('href', '?')}"})
                body = b'{"ok":true}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self._cors()
                self.end_headers()
                self.wfile.write(body)
                return
            if path == "/type":
                HUB.publish("text", {"text": str(payload.get("text", ""))})
                body = b'{"ok":true}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self._cors()
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_error(404)

    return Handler


def start_server(port: int = 8765) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(port))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    HUB.status = "running"
    HUB.publish("status", {"text": "server online"})
    return server


def stream_text(text: str, cps: float = 18.0) -> None:
    HUB.publish("clear", {})
    delay = 1.0 / max(cps, 1.0)
    for ch in text:
        HUB.publish("char", {"ch": ch})
        time.sleep(delay)
