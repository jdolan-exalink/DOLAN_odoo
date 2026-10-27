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
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".o_dolan_rail", { timeout: 25000 });
await page.waitForTimeout(3000);
const rail = await page.evaluate(() => [...document.querySelectorAll(".o_dolan_rail [data-menu-xmlid]")].map((e) => e.getAttribute("data-menu-xmlid")));
console.log("RAIL n:", rail.length, "| tiene fleet/mrp/pos/ai:", rail.filter((x) => /fleet|mrp|point_of_sale|DOLAN_ai/.test(x)));
await page.locator('[data-menu-xmlid="stock.menu_stock_root"]').first().click();
await page.waitForTimeout(6000);
const inv = await page.evaluate(() => [...document.querySelectorAll(".o_card_record a.oe_kanban_action")].map((e) => e.textContent.trim()));
console.log("INV titles:", JSON.stringify(inv));
await page.screenshot({ path: `${SHOTS}/s6-inventario.png` });
await page.locator('[data-menu-xmlid="purchase.menu_purchase_root"]').first().click();
await page.waitForTimeout(5500);
const sample = await page.evaluate(() => {
  const rows = [...document.querySelectorAll(".o_view_sample_data .o_list_table .o_data_row")];
  return { n: rows.length, op: rows[0] ? getComputedStyle(rows[0]).opacity : null };
});
console.log("SAMPLE rows:", JSON.stringify(sample));
await page.screenshot({ path: `${SHOTS}/s6-compras.png` });
console.log("CONSOLE claro:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 3)) : "(sin errores)");
await browser.close();
