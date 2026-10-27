import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 140)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector("[data-menu-xmlid]", { timeout: 25000 });
await page.waitForTimeout(2500);

// 1) Inventario por xmlid
try {
  await page.locator('[data-menu-xmlid="stock.menu_stock_root"]').first().click({ timeout: 8000 });
  await page.waitForTimeout(5500);
  await page.screenshot({ path: "shots/dash/inventario.png" });
  console.log("OK inventario");
  // productos: submenu dentro de Inventario
  const prod = page.getByText("Productos", { exact: true }).first();
  if (await prod.count()) { await prod.click().catch(() => {}); await page.waitForTimeout(4000); await page.screenshot({ path: "shots/dash/productos.png" }); console.log("OK productos (submenu)"); }
} catch (e) { console.log("FAIL inventario:", String(e).slice(0, 100)); }

// 2) Apps dialog -> qué apps lista realmente
try {
  await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2500);
  await page.locator('[data-menu-xmlid="base.menu_management"]').first().click({ timeout: 8000 });
  await page.waitForTimeout(2500);
  const dlg = await page.evaluate(() =>
    [...document.querySelectorAll(".o_app, .o_menu_item, [data-menu-xmlid]")].map((e) => (e.getAttribute("title") || e.textContent || "").trim().slice(0, 30)).filter(Boolean).slice(0, 40)
  );
  console.log("APPS_DIALOG:", JSON.stringify(dlg));
  await page.screenshot({ path: "shots/dash/apps-grid.png" });
  // 3) Flotilla desde el dialogo
  const fl = page.getByText(/Flotilla|Fleet/).first();
  if (await fl.count()) { await fl.click().catch(() => {}); await page.waitForTimeout(5500); await page.screenshot({ path: "shots/dash/flotilla.png" }); console.log("OK flotilla"); }
  else console.log("SIN APP flotilla en dialogo");
} catch (e) { console.log("FAIL apps/flotilla:", String(e).slice(0, 120)); }

console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 5)) : "(sin errores)");
await browser.close();
