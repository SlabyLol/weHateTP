from __future__ import annotations

INJECT_JS = r"""
(function () {
  if (window.__typebotInjected) {
    console.log("[TypeBot] already present");
    return;
  }
  window.__typebotInjected = true;
  const box = document.createElement("div");
  box.id = "typebot-overlay";
  box.setAttribute("data-author", "DarkFox");
  box.style.cssText = [
    "position:fixed","top:14px","right:14px","z-index:2147483647",
    "background:#0d0d0d","color:#ff1a1a",
    "font-family:'Courier New',Courier,monospace","font-size:15px","line-height:1.25",
    "padding:10px 16px","border:2px solid #ff1a1a","border-radius:8px",
    "box-shadow:0 0 18px rgba(255,0,0,0.45), inset 0 0 8px rgba(255,0,0,0.15)",
    "opacity:0","transform:translateY(-8px)",
    "transition:opacity 0.45s ease, transform 0.45s ease",
    "pointer-events:none","user-select:none","letter-spacing:0.5px"
  ].join(";");
  box.innerHTML =
    '<div style="font-weight:700;font-size:16px;color:#ff1a1a;">TypeBot</div>' +
    '<div style="font-size:11px;color:#b0b0b0;margin-top:3px;font-weight:400;">By DarkFox</div>';
  (document.documentElement || document.body).appendChild(box);
  requestAnimationFrame(() => {
    box.style.opacity = "1";
    box.style.transform = "translateY(0)";
  });
  setTimeout(() => {
    box.style.opacity = "0";
    box.style.transform = "translateY(-6px)";
    setTimeout(() => {
      box.remove();
      delete window.__typebotInjected;
    }, 500);
  }, 5000);
  console.log("%c[TypeBot] injected by DarkFox – visible 5s", "color:#ff1a1a;font-weight:bold");
})();
""".strip()


def get_inject_script() -> str:
    return INJECT_JS


def get_bookmarklet() -> str:
    compact = " ".join(line.strip() for line in INJECT_JS.splitlines() if line.strip())
    return "javascript:" + compact
