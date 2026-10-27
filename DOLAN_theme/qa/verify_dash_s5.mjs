import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 120)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".o_dolan_rail", { timeout: 25000 });
await page.waitForTimeout(2500);
const chip = await page.evaluate(() => {
  const c = [...document.querySelectorAll(".o_main_navbar .o_nav_entry")].filter(e => !e.closest(".o_dolan_rail"))[0];
  const cs = c ? getComputedStyle(c) : null;
  return { txt: c ? c.textContent.trim().slice(0, 14) : null, bg: cs ? cs.backgroundColor : null, color: cs ? cs.color : null,
           rail: document.querySelectorAll(".o_dolan_rail .o_dolan_rail_item").length };
});
console.log("CHIP:", JSON.stringify(chip));
const apps = [["compras", "purchase.menu_purchase_root"], ["inventario", "stock.menu_stock_root"], ["mantenimiento", "maintenance.menu_maintenance_title"]];
for (const [slug, xml] of apps) {
  await page.locator(`[data-menu-xmlid="${xml}"]`).first().click();
  await page.waitForTimeout(6000);
  await page.screenshot({ path: `shots/dash/s5-${slug}.png` });
  console.log("SHOT claro:", slug);
}
// oscuro: inyectar atributo y reencuadrar compras + inventario
await page.evaluate(() => { document.documentElement.setAttribute("data-dolan-theme", "dark"); });
for (const [slug, xml] of [["compras", "purchase.menu_purchase_root"], ["inventario", "stock.menu_stock_root"]]) {
  await page.locator(`[data-menu-xmlid="${xml}"]`).first().click();
  await page.waitForTimeout(5000);
  await page.screenshot({ path: `shots/dash/s5-${slug}-dark.png` });
  console.log("SHOT oscuro:", slug);
}
console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 5)) : "(sin errores)");
await browser.close();
