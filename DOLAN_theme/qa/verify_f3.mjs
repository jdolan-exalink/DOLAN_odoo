import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const SHOTS = "/root/DOLAN_odoo20/DOLAN_theme/qa/shots";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 110)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
// 1) apps nuevas en el rail
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector("[data-menu-xmlid]", { timeout: 25000 });
await page.waitForTimeout(2500);
const rail = await page.evaluate(() => [...document.querySelectorAll(".o_dolan_rail [data-menu-xmlid]")].map((e) => e.getAttribute("data-menu-xmlid")));
console.log("RAIL n:", rail.length, "| nuevos:", JSON.stringify(rail.filter((x) => /alquiler|suscrip|calidad/i.test(x))));
// 2) scan real
const code = process.env.SCAN_CODE || "";
const r = await page.goto(`${BASE}/dolan_codigo_barras`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(1200);
if (code) {
  await page.fill("#scan", code);
  await page.press("#scan", "Enter");
  await page.waitForTimeout(2000);
}
const out = await page.evaluate(() => document.getElementById("out").textContent.trim().slice(0, 140));
console.log("SCAN status:", r.status(), "| out:", JSON.stringify(out));
await page.screenshot({ path: `${SHOTS}/f3-escaneo.png` });
// 3) apps nuevos accesibles (act_url) — probamos la de calidad
const rc = await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 4)) : "(sin errores)");
await browser.close();
