"""F5 — PRD04: evaluated PWA behaviour (installable manifest + a conservative
service worker: cache-first only for versioned assets, network-first for
navigations). No intrusive offline app in this first stage."""
import json

from odoo import http
from odoo.http import request

SW_JS = r"""
const CACHE = 'dolan-pwa-v1';
self.addEventListener('install', (e) => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  const versioned = url.pathname.startsWith('/web/assets/')
    || /\.[0-9a-f]{6,}\.(js|css|png|svg|jpe?g|webp|woff2?)$/.test(url.pathname);
  if (versioned) {
    e.respondWith(caches.open(CACHE).then(async (c) => {
      const hit = await c.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res && res.ok) c.put(req, res.clone());
      return res;
    }));
    return;
  }
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).then((r) => r).catch(async () => {
      const cached = await caches.match(req);
      return cached || caches.match('/odoo') || Response.error();
    }));
  }
});
"""


class DolanPwa(http.Controller):

    @http.route("/dolan_theme/manifest.webmanifest", type="http", auth="user",
                methods=["GET"], csrf=False, sitemap=False)
    def manifest(self):
        logo = "/web/image/res.company/%s/logo" % request.env.company.id
        data = {
            "name": "%s — Odoo" % request.env.company.name,
            "short_name": "DOLAN",
            "start_url": "/odoo",
            "scope": "/",
            "display": "standalone",
            "orientation": "any",
            "background_color": "#1a1a2e",
            "theme_color": "#4338ca",
            "icons": [
                {"src": logo, "sizes": "any", "purpose": "any", "type": "image/png"},
                {"src": logo, "sizes": "any", "purpose": "maskable", "type": "image/png"},
            ],
        }
        return request.make_response(
            json.dumps(data),
            headers=[("Content-Type", "application/manifest+json"),
                     ("Cache-Control", "no-store")])

    @http.route("/dolan_theme/dolan-sw.js", type="http", auth="user",
                methods=["GET"], csrf=False, sitemap=False)
    def service_worker(self):
        return request.make_response(
            SW_JS,
            headers=[("Content-Type", "application/javascript; charset=utf-8"),
                     ("Cache-Control", "no-cache"),
                     ("Service-Worker-Allowed", "/")])
