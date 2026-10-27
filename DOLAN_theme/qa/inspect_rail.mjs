// Inspecccion DOLAN_theme: rail de apps — DOM real + consola del navegador
// Uso: node inspect_rail.mjs  (requiere Playwright + Chromium)
import { chromium } from "playwright";
import { mkdirSync } from "fs";

const BASE = process.env.ODOO_URL || "http://localhost:8070";
const outDir = new URL("./shots/", import.meta.url).pathname;
mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const consoleMsgs = [];
page.on("console", (m) => {
  if (["error", "warning"].includes(m.type())) consoleMsgs.push(`[${m.type()}] ${m.text().slice(0, 300)}`);
});
page.on("pageerror", (e) => consoleMsgs.push(`[pageerror] ${String(e).slice(0, 400)}`));

// sesion via JSON-RPC (mismo camino que el cliente real, sin el form de login)
const auth = await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
console.log("AUTH:", auth.status());
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
// SPA con long-poll: esperar el rail (o 30s) en vez de networkidle
try {
  await page.waitForSelector(".o_dolan_rail", { timeout: 30000 });
} catch {
  console.log("RAIL no aparecio en 30s");
}
await page.waitForTimeout(3000);

// rail presente?
const railCount = await page.locator(".o_dolan_rail").count();
console.log("RAIL presente:", railCount);

if (railCount) {
  const info = await page.evaluate(() => {
    const items = [...document.querySelectorAll(".o_dolan_rail .o_dolan_rail_item")];
    return items.map((a) => {
      const img = a.querySelector("img.o_dolan_rail_icon");
      const ico = a.querySelector("i.o_dolan_rail_ico");
      const span = a.querySelector(".o_dolan_rail_label");
      return {
        label: (span?.textContent || "").trim().slice(0, 30),
        img: img ? { src: (img.getAttribute("src") || "").slice(0, 40), natural: img.naturalWidth } : null,
        iTag: !!ico,
        active: a.classList.contains("o_dolan_rail_active"),
        visible: a.offsetParent !== null,
      };
    });
  });
  console.log("ITEMS:", JSON.stringify(info, null, 1).slice(0, 3000));
}

console.log("CONSOLE:", consoleMsgs.length ? consoleMsgs.slice(0, 12) : "(sin errores)");
await page.screenshot({ path: outDir + "rail.png", fullPage: false });
console.log("SHOT:", outDir + "rail.png");
await browser.close();
