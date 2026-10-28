import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const SHOTS = "/root/DOLAN_odoo20/DOLAN_theme/qa/shots";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text()); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
// A) hr: error completo
await page.goto(`${BASE}/odoo/action-544`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(6000);
console.log("HR errs:", JSON.stringify([...new Set(errs)].map((e) => e.slice(0, 400))));
errs.length = 0;
// B) POS dashboard + restaurant
await page.goto(`${BASE}/odoo/action-728`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(6500);
const pos = await page.evaluate(() => ({
  titulo: document.title.slice(0, 50),
  cajas: document.querySelectorAll(".o_kanban_record, .o_data_row").length,
}));
await page.screenshot({ path: `${SHOTS}/f5-pos.png` });
console.log("POS:", JSON.stringify(pos), "| errs:", JSON.stringify([...new Set(errs)].map((e) => e.slice(0, 200))));
errs.length = 0;
// pos_restaurant (action-1100)
await page.goto(`${BASE}/odoo/action-1100`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(5500);
const rest = await page.evaluate(() => ({ titulo: document.title.slice(0, 50) }));
await page.screenshot({ path: `${SHOTS}/f5-pos-restaurante.png` });
console.log("RESTAURANT:", JSON.stringify(rest), "| errs:", JSON.stringify([...new Set(errs)].map((e) => e.slice(0, 250))));
console.log("DONE");
await browser.close();
