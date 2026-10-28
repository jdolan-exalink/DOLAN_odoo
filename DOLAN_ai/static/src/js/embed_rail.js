/** Rail embebido para páginas HTML propias (/dolan_*) — visible en cualquier página suelta. */
(function () {
  "use strict";
  var CSS = ".o_dolan_rail{position:fixed;top:0;left:0;bottom:0;width:240px;background:#fff;border-right:1px solid #e5e7eb;box-shadow:4px 0 16px rgba(15,23,42,.06);overflow-y:auto;padding:12px 0;z-index:30;display:flex;flex-direction:column}" +
    ".o_dolan_rail_title{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;font-weight:700;padding:6px 16px 10px}" +
    ".o_dolan_rail_item{display:flex;align-items:center;gap:10px;padding:9px 14px;margin:1px 8px;border-radius:8px;color:#1f2937;text-decoration:none}" +
    ".o_dolan_rail_item:hover{background:#eef2ff;color:#4338ca}" +
    ".o_dolan_rail_item.o_dolan_rail_active{background:#eef2ff;color:#4338ca;font-weight:700;box-shadow:inset 3px 0 0 #714b67}" +
    ".o_dolan_rail_item img{width:24px;height:24px;border-radius:6px}" +
    ".o_dolan_rail_item span{font-size:13.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
    "body{padding-left:240px !important}" +
    "@media (max-width:992px){.o_dolan_rail{display:none}body{padding-left:0 !important}}";
  var DARK = ".o_dolan_rail{background:#1e293b;border-color:#334155}.o_dolan_rail_item{color:#e2e8f0}.o_dolan_rail_title{color:#94a3b8}.o_dolan_rail_item:hover,.o_dolan_rail_item.o_dolan_rail_active{background:#334155;color:#fff}";
  function build(menus) {
    var rail = document.createElement("div");
    rail.className = "o_dolan_rail";
    var t = document.createElement("div");
    t.className = "o_dolan_rail_title";
    t.textContent = "APLICACIONES";
    rail.appendChild(t);
    var here = location.pathname;
    var ids = Object.keys(menus).filter(function (k) { return !isNaN(k); });
    ids.sort(function (a, b) { return (menus[a].sequence || 0) - (menus[b].sequence || 0); });
    ids.forEach(function (k) {
      var m = menus[k];
      var a = document.createElement("a");
      a.className = "o_dolan_rail_item";
      a.href = "/odoo/action-" + (m.actionID || m.id);
      if (m.webIconData) { var img = document.createElement("img"); img.src = m.webIconData; a.appendChild(img); }
      var sp = document.createElement("span"); sp.textContent = m.name; a.appendChild(sp);
      rail.appendChild(a);
    });
    document.body.appendChild(rail);
  }
  function init() {
    var st = document.createElement("style");
    st.textContent = CSS + (document.documentElement.dataset.dolanTheme === "dark" ? DARK : "");
    document.head.appendChild(st);
    fetch("/web/dataset/call_kw", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: { model: "ir.ui.menu", method: "load_menus", args: [false], kwargs: {} } }),
      credentials: "same-origin",
    }).then(function (r) { return r.json(); }).then(function (j) { build(j.result || {}); });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
