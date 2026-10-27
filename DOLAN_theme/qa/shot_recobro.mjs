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
await page.locator('.o_dolan_rail_item[data-menu-xmlid="dolan_dash.menu_operaciones_root"]').click();
await page.waitForTimeout(1200);
await page.getByText("Listados", { exact: true }).first().click();
await page.waitForTimeout(3000);
const r = await page.evaluate(() => {
  const cols = [...document.querySelectorAll(".o_list_table thead th")].map((t) => t.textContent.trim());
  const idx = cols.findIndex((c) => c.includes("recobro"));
  const filas = idx >= 0 ? [...document.querySelectorAll(".o_list_table .o_data_row")].slice(0, 4)
    .map((f) => (f.querySelectorAll("td")[idx]?.textContent || "").trim()) : [];
  return { cols, idx, filas, nfilas: document.querySelectorAll(".o_list_table .o_data_row").length,
    badges: document.querySelectorAll(".o_list_table .badge").length };
});
console.log("RECOBRO:", JSON.stringify(r));
await page.screenshot({ path: "shots/lista-ultimo-recobro.png" });
console.log("CONSOLE:", errs.length ? errs : "(sin errores)");
await browser.close();
