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

// 1) Listados (lista de compras)
await page.getByText("Listados", { exact: true }).first().click();
await page.waitForSelector(".o_list_table", { timeout: 20000 });
await page.waitForTimeout(1200);
await page.screenshot({ path: "shots/lista-compras.png" });

// 2) Formulario de factura (primer comprobante)
await page.locator(".o_list_table .o_data_row").first().click();
await page.waitForSelector(".o_form_sheet", { timeout: 20000 });
await page.waitForTimeout(1000);
await page.screenshot({ path: "shots/form-factura.png" });

// 3) Contactos -> lista -> formulario
await page.locator('.o_dolan_rail_item[data-menu-xmlid="contacts.menu_contacts"]').click();
await page.waitForTimeout(1500);
try { await page.locator(".o_list_table .o_data_row").first().click({ timeout: 5000 }); } catch {}
await page.waitForSelector(".o_form_sheet", { timeout: 20000 });
await page.waitForTimeout(1000);
await page.screenshot({ path: "shots/form-contacto.png" });

console.log("CONSOLE:", errs.length ? errs : "(sin errores)");
await browser.close();
