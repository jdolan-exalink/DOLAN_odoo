from odoo import http
from odoo.http import request

PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <title>DOLAN — Aplicaciones</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
</head>
<body>
  <a href="/odoo" style="position:fixed;top:14px;left:16px;z-index:20;display:inline-flex;align-items:center;gap:6px;text-decoration:none;color:#4338ca;background:#fff;border:1px solid #e5e7eb;border-radius:999px;padding:7px 14px;font-family:system-ui,sans-serif;font-size:13px;font-weight:600;box-shadow:0 2px 8px rgba(0,0,0,.06)">&#8592; Volver a Odoo</a>
  <button id="theme-toggle" type="button" aria-label="Cambiar modo claro u oscuro" title="Cambiar modo claro u oscuro">🌓</button>
  <div style="display:flex;justify-content:center;padding:60px 40px;flex-wrap:wrap;gap:28px 16px;align-content:flex-start;max-width:900px;margin:0 auto" id="apps-grid"></div>
  <style>
    body{font-family:system-ui,sans-serif;margin:0;background:#f4f6f9;color:#1f2937;min-height:100vh}
    #theme-toggle{position:fixed;top:16px;right:20px;z-index:1050;border:1px solid #d1d5db;background:#fff;border-radius:999px;width:42px;height:42px;cursor:pointer;font-size:19px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
    #theme-toggle:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,.14)}
    .o_dolan_home_app{display:flex;flex-direction:column;align-items:center;text-decoration:none!important;cursor:pointer;transition:transform .15s ease;width:130px}
    .o_dolan_home_app:hover{transform:translateY(-3px)}
    .o_dolan_home_app:hover .icon_wrap{box-shadow:0 8px 24px rgba(0,0,0,.14)}
    .o_dolan_home_app:hover .name{color:#714b67}
    .icon_wrap{width:82px;height:82px;background:#fff;border-radius:16px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 10px rgba(0,0,0,.08);margin-bottom:10px;overflow:hidden;transition:box-shadow .15s,transform .15s}
    .icon_wrap img{width:70px;height:70px;object-fit:contain;border-radius:8px}
    .name{font-size:13px;font-weight:600;color:#1f2937;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:130px;transition:color .15s}
    html[data-dolan-theme="dark"] body{background:#1a1a2e;color:#e2e8f0}
    html[data-dolan-theme="dark"] .icon_wrap{background:#2a2a4a;box-shadow:0 2px 10px rgba(0,0,0,.3)}
    html[data-dolan-theme="dark"] .name{color:#e2e8f0}
    html[data-dolan-theme="dark"] #theme-toggle{background:#2a2a4a;color:#e2e8f0;border-color:#40406a}
  </style>
  <script>
  document.addEventListener("DOMContentLoaded", function() {
    var root = document.documentElement;
    try {
      var savedTheme = localStorage.getItem("dolan_theme_mode");
      if (savedTheme === "dark" || savedTheme === "light") root.dataset.dolanTheme = savedTheme;
    } catch (_error) {}
    document.getElementById("theme-toggle").addEventListener("click", function() {
      var next = root.dataset.dolanTheme === "dark" ? "light" : "dark";
      root.dataset.dolanTheme = next;
      try { localStorage.setItem("dolan_theme_mode", next); } catch (_error) {}
    });
    fetch("/web/webclient/load_menus", { credentials: "same-origin" })
      .then(function(r) { return r.json(); })
      .then(function(j) {
        var res = j.result || j;
        var root = res.root || {};
        var grid = document.getElementById("apps-grid");
        (root.children || []).forEach(function(cid) {
          var m = res[cid];
          if (!m || m.appID !== m.id) return;
          var a = document.createElement("a");
          a.className = "o_dolan_home_app";
          a.href = "/odoo/" + (m.actionPath || "action-" + m.actionID);
          var wrap = document.createElement("div"); wrap.className = "icon_wrap";
          if (m.webIconData) {
            var img = document.createElement("img"); img.src = m.webIconData; wrap.appendChild(img);
          } else if (m.webIcon && m.webIcon.indexOf(",") > -1) {
            var parts = m.webIcon.split(",");
            var i = document.createElement("i"); i.className = "oi";
            i.setAttribute("data-icon", parts[0]); i.style.cssText = "font-size:36px;color:" + (parts[1] || "#714b67");
            wrap.appendChild(i);
          }
          a.appendChild(wrap);
          var sp = document.createElement("span"); sp.className = "name"; sp.textContent = m.name;
          a.appendChild(sp);
          grid.appendChild(a);
        });
      });
  });
  </script>
</body>
</html>"""

class DolanHomeGrid(http.Controller):
    @http.route("/dolan_apps", type="http", auth="user", methods=["GET"], csrf=False, sitemap=False)
    def home_grid(self, **kw):
        return request.make_response(PAGE,
            headers=[("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-store")])
