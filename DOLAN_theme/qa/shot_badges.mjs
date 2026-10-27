import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 150)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".o_dolan_dash", { timeout: 25000 });
// volvemos a Operaciones y abrimos Listados
await page.locator('.o_dolan_rail_item[data-menu-xmlid="dolan_dash.menu_operaciones_root"]').click();
await page.waitForTimeout(1200);
await page.getByText("Listados", { exact: true }).first().click();
await page.waitForTimeout(2500);
const badges = await page.evaluate(() => {
  const cells = [...document.querySelectorAll(".o_list_table .badge")];
  const cols = [...document.querySelectorAll(".o_list_table thead th")].map((t) => t.textContent.trim()).slice(0, 8);
  return { n: cells.length, ejemplos: cells.slice(0, 4).map((b) => b.textContent.trim()), cols };
});
console.log("BADGES:", JSON.stringify(badges));
await page.screenshot({ path: "shots/lista-badge.png" });
console.log("CONSOLE:", errs.length ? errs : "(sin errores)");
await browser.close();
