from __future__ import annotations

import json
import queue
import threading
import time
import uuid
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
        self.from_js: queue.Queue = queue.Queue(maxsize=500)
        self.session = str(uuid.uuid4())[:8]

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=300)
        with self.lock:
            self.subscribers.append(q)
            self.clients = len(self.subscribers)
            for item in self.history[-40:]:
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
        msg = {"id": str(uuid.uuid4())[:8], "event": event, "data": data or {}, "ts": time.time(), "session": self.session}
        with self.lock:
            self.history.append(msg)
            if len(self.history) > 120:
                self.history = self.history[-120:]
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

    def recv_from_js(self, payload: Dict[str, Any]) -> None:
        try:
            self.from_js.put_nowait(payload)
        except queue.Full:
            pass

    def drain_js(self) -> List[Dict[str, Any]]:
        items = []
        while True:
            try:
                items.append(self.from_js.get_nowait())
            except queue.Empty:
                break
        return items


HUB = Hub()

INJECT_JS = r"""
(function () {
  if (window.__typebotLive) { console.log("[TypeBot] already live"); return; }
  window.__typebotLive = true;
  const PORT = __PORT__;
  const BASE = "http://127.0.0.1:" + PORT;
  const clientId = "js-" + Math.random().toString(36).slice(2, 10);
  const box = document.createElement("div");
  box.id = "typebot-live";
  box.style.cssText = ["position:fixed","top:14px","right:14px","z-index:2147483647","min-width:240px","max-width:380px","background:#0d0d0d","color:#ff1a1a","font-family:'Courier New',Courier,monospace","font-size:14px","line-height:1.4","padding:12px 16px","border:2px solid #ff1a1a","border-radius:8px","box-shadow:0 0 20px rgba(255,0,0,0.5)","pointer-events:auto","user-select:none"].join(";");
  box.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;"><div style="font-weight:700;font-size:16px;color:#ff1a1a;">TypeBot</div><div id="tb-dot" style="width:8px;height:8px;border-radius:50%;background:#666;"></div></div><div style="font-size:11px;color:#b0b0b0;margin:2px 0 6px;">By DarkFox · LIVE</div><div id="tb-status" style="font-size:11px;color:#888;margin-bottom:6px;">booting…</div><div id="tb-text" style="color:#fff;font-size:13px;min-height:1.3em;white-space:pre-wrap;word-break:break-word;"></div><div id="tb-cursor" style="display:inline-block;width:8px;height:14px;background:#ff1a1a;margin-left:1px;vertical-align:text-bottom;animation:tbblink 1s step-end infinite;"></div>';
  if (!document.getElementById("tb-style")) { var st=document.createElement("style"); st.id="tb-style"; st.textContent="@keyframes tbblink{50%{opacity:0}}"; document.documentElement.appendChild(st); }
  (document.documentElement||document.body).appendChild(box);
  const statusEl=document.getElementById("tb-status");
  const textEl=document.getElementById("tb-text");
  const dotEl=document.getElementById("tb-dot");
  let full=""; let es=null;
  function setDot(ok){ dotEl.style.background=ok?"#4caf50":"#ff9800"; dotEl.style.boxShadow=ok?"0 0 6px #4caf50":"0 0 6px #ff9800"; }
  function setStatus(s,ok){ statusEl.textContent=s; statusEl.style.color=ok?"#4caf50":"#ff9800"; setDot(!!ok); }
  function send(event,data){
    return fetch(BASE+"/from-js",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({clientId:clientId,event:event,data:data||{},href:location.href,ts:Date.now()})}).catch(function(){return null;});
  }
  function apply(msg){
    if(!msg||!msg.event)return;
    var e=msg.event,d=msg.data||{};
    if(e==="status")setStatus(d.text||"live",true);
    if(e==="clear"){full="";textEl.textContent="";}
    if(e==="char"){full+=(d.ch!=null?d.ch:"");textEl.textContent=full;}
    if(e==="text"){full=d.text!=null?String(d.text):"";textEl.textContent=full;}
    if(e==="line"){full+=(d.text!=null?String(d.text):"")+"\n";textEl.textContent=full;}
    if(e==="ping")send("pong",{pingId:d.id||null});
    if(e==="ack")setStatus("python ok · "+(d.msg||"ack"),true);
    send("ack",{msgId:msg.id,event:e});
  }
  function connectSSE(){
    if(es){try{es.close();}catch(e){}}
    es=new EventSource(BASE+"/events?client="+encodeURIComponent(clientId));
    es.onopen=function(){ setStatus("connected · live",true); send("hello",{ua:navigator.userAgent,title:document.title}); };
    es.onmessage=function(ev){ try{apply(JSON.parse(ev.data));}catch(err){} };
    es.onerror=function(){ setStatus("reconnecting…",false); try{es.close();}catch(e){}; setTimeout(connectSSE,1200); };
  }
  setInterval(function(){ send("heartbeat",{fullLen:full.length}); },4000);
  connectSSE();
  console.log("%c[TypeBot] LIVE bridge "+clientId+" → :"+PORT,"color:#ff1a1a;font-weight:bold");
  window.TypeBot={send:send,clear:function(){full="";textEl.textContent="";send("clear",{});},status:function(){return{clientId:clientId,text:full};}};
})();
"""

DEMO_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>TypeBot LIVE · weHateTP</title>
<style>body{margin:0;background:#111;color:#eee;font-family:system-ui,sans-serif}main{max-width:640px;margin:48px auto;padding:24px}h1{color:#ff1a1a;font-family:'Courier New',monospace}p{color:#aaa;line-height:1.5}code{background:#222;padding:2px 6px;border-radius:4px;color:#ff8a80}</style>
</head><body><main><h1>TypeBot LIVE</h1><p>JS <-> Python bridge active. Overlay top-right.</p><p>Server: <code id="srv"></code></p></main>
<script>document.getElementById("srv").textContent=location.origin;</script>
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
                self.send_header("Cache-Control", "no-store")
                self._cors()
                self.end_headers()
                self.wfile.write(js)
                return
            if path == "/status":
                data = json.dumps({"status": HUB.status, "clients": HUB.clients, "session": HUB.session}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self._cors()
                self.end_headers()
                self.wfile.write(data)
                return
            if path == "/events":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self._cors()
                self.end_headers()
                q = HUB.subscribe()
                try:
                    hello = {"event": "status", "data": {"text": "sse open"}, "id": "0", "session": HUB.session}
                    self.wfile.write(f"data: {json.dumps(hello)}\n\n".encode())
                    self.wfile.flush()
                    while True:
                        try:
                            msg = q.get(timeout=12)
                            self.wfile.write(f"data: {json.dumps(msg)}\n\n".encode())
                            self.wfile.flush()
                        except queue.Empty:
                            ping = {"event": "ping", "data": {"id": str(time.time())}, "ts": time.time()}
                            self.wfile.write(f"data: {json.dumps(ping)}\n\n".encode())
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
            if path in ("/from-js", "/hello", "/type"):
                HUB.recv_from_js(payload)
                if payload.get("event") == "hello":
                    cid = payload.get("clientId", "?")
                    HUB.publish("ack", {"msg": f"hello {cid}"})
                    HUB.publish("status", {"text": f"js online · {cid}"})
                body = json.dumps({"ok": True, "session": HUB.session}).encode()
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
    HUB.publish("status", {"text": "typed · live"})
