import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const mode = process.argv[2] || "claro";
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
const probe = await page.evaluate(() => {
  const dd = [...document.querySelectorAll(".o_main_navbar .o-dropdown.dropdown-toggle")].filter(e => !e.closest(".o_dolan_rail")).slice(0, 3)
    .map(e => ({ txt: e.textContent.trim().slice(0, 12), bg: getComputedStyle(e).backgroundColor }));
  return { dropdowns: dd, tema: document.documentElement.dataset.dolanTheme || "(sin attr)" };
});
console.log(`PROBE[${mode}]:`, JSON.stringify(probe));
const targets = mode === "oscuro"
  ? [["compras", "purchase.menu_purchase_root"], ["inventario", "stock.menu_stock_root"], ["mantenimiento", "maintenance.menu_maintenance_title"]]
  : [["mantenimiento", "maintenance.menu_maintenance_title"], ["compras", "purchase.menu_purchase_root"]];
for (const [slug, xml] of targets) {
  await page.locator(`[data-menu-xmlid="${xml}"]`).first().click();
  await page.waitForTimeout(5500);
  await page.screenshot({ path: `shots/dash/s5b-${slug}${mode === "oscuro" ? "-dark" : ""}.png` });
  console.log("SHOT:", mode, slug);
}
console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 4)) : "(sin errores)");
await browser.close();
