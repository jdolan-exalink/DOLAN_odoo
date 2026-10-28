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
for (const [slug, url] of [["mantenimiento", "/dolan_mantenimiento"], ["flotilla", "/dolan_flotilla"], ["contabilidad", "/dolan_contabilidad"]]) {
  const r = await page.goto(BASE + url, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2500);
  const cards = await page.evaluate(() => [...document.querySelectorAll("#kpis div div")].map((e) => e.textContent.trim()).slice(0, 14));
  console.log(slug.toUpperCase(), "status:", r.status(), "| cards:", JSON.stringify(cards));
  await page.screenshot({ path: `${SHOTS}/f2-${slug}.png` });
}
console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 4)) : "(sin errores)");
await browser.close();
