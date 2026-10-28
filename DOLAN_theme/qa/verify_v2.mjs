import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const SHOTS = "/root/DOLAN_odoo20/DOLAN_theme/qa/shots";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 860 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 110)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
for (const [slug, url] of [["alq", "/dolan_alquileres"], ["subs", "/dolan_suscripciones"]]) {
  const r = await page.goto(BASE + url, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2200);
  const cards = await page.evaluate(() => [...document.querySelectorAll("#kpis div div")].map((e) => e.textContent.trim()).slice(0, 12));
  console.log(slug.toUpperCase(), "status:", r.status(), "| cards:", JSON.stringify(cards));
  await page.screenshot({ path: `${SHOTS}/v2-${slug}.png` });
}
// barras v2: layout + modos + scan real
const rb = await page.goto(`${BASE}/dolan_codigo_barras`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(1800);
const modes = await page.evaluate(() => ({
  op: document.getElementById("btn-op")?.getAttribute("href"),
  inv: document.getElementById("btn-inv")?.getAttribute("href"),
  tips: document.querySelectorAll("ul li").length,
}));
console.log("BARRAS status:", rb.status(), "| modos:", JSON.stringify(modes));
await page.fill("#scan", "PRD-001");
await page.press("#scan", "Enter");
await page.waitForTimeout(1800);
const out = await page.evaluate(() => document.getElementById("out").textContent.trim().slice(0, 120));
console.log("SCAN:", JSON.stringify(out));
await page.screenshot({ path: `${SHOTS}/v2-barras.png` });
console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 4)) : "(sin errores)");
await browser.close();
