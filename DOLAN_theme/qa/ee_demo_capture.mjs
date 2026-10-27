// Captura de REFERENCIA de la demo Enterprise (patrones UX, sin extraer código).
// Credenciales SOLO por variables de entorno (no en este archivo).
import { chromium } from "playwright";

const BASE = process.env.EE_BASE || "https://exalink.odoo.com";
const USER = process.env.EE_USER;
const PASS = process.env.EE_PASS;
const OUT = "/root/odoo20/DOLAN_theme/docs/evidence/ee-demo/";
if (!USER || !PASS) { console.error("FALTAN CREDENCIALES"); process.exit(2); }

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("pageerror", (e) => errs.push(String(e).slice(0, 200)));

await page.goto(BASE + "/web/login", { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(2500);
console.log("LOGIN PAGE:", page.url());

// formulario de login SaaS (sin selector de db en subdominio)
const dbSel = page.locator('select[name="db"]');
if (await dbSel.count()) await dbSel.selectOption({ index: 0 }).catch(() => {});
await page.fill('#login, input[name="login"]', USER);
await page.fill('#password, input[name="password"]', PASS);
await Promise.all([
  page.waitForURL(/\/odoo|\/web#|web\/session/, { timeout: 45000 }).catch(() => {}),
  page.click('button[type="submit"]'),
]);
await page.waitForTimeout(6000);
console.log("POST-LOGIN:", page.url());
await page.screenshot({ path: OUT + "00-home.png" });

// tile de Facturacion en la home EE
await page.getByText("Facturación", { exact: true }).first().click();
await page.waitForTimeout(7000);
console.log("TRAS TILE:", page.url());
await page.screenshot({ path: OUT + "01-dashboard-facturacion.png" });

// secciones del menu superior de contabilidad (dashboard/facturas/...)

const secciones = await page.evaluate(() => ({
  nav: [...document.querySelectorAll(".o_menu_sections a, .o_menu_sections button")].map((x) => x.textContent.trim()),
  breadcrumb: document.querySelector(".o_breadcrumb")?.textContent.trim().slice(0, 120),
}));
console.log("SECCIONES:", JSON.stringify(secciones));

// seccion Clientes = BUTTON (dropdown): click -> child Facturas
const btnCli = page.locator('button:has-text("Clientes"), [role="button"]:has-text("Clientes")');
console.log("btnCli count:", await btnCli.count());
if (await btnCli.count()) { await btnCli.first().click().catch(() => {}); await page.waitForTimeout(2000); }
const child = page.locator('a, button').filter({ hasText: /^Facturas$/ });
console.log("child Facturas count:", await child.count());
if (await child.count()) { await child.first().click().catch(() => {}); await page.waitForTimeout(6000); }
console.log("TRAS FACTURAS:", page.url());
await page.screenshot({ path: OUT + "02-lista-facturas.png" });

// si no hay lista, abrir NUEVO -> Factura (formularion EE directo)
const filas = await page.locator(".o_data_row").count();
console.log("filas lista:", filas);
if (!filas) {
  // volver al tablero y usar "Nuevo"
  await page.goto(BASE + "/odoo/accounting", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  const nuevo = page.locator('button:has-text("Nuevo")');
  console.log("btn Nuevo:", await nuevo.count());
  if (await nuevo.count()) {
    await nuevo.first().click();
    await page.waitForTimeout(2500);
    const item = page.locator('a, button').filter({ hasText: /Factura$| factura/ }).first();
    if (await item.count()) { await item.click().catch(() => {}); await page.waitForTimeout(7000); }
  }
  console.log("TRAS NUEVO:", page.url());
  await page.screenshot({ path: OUT + "03-formulario.png" });
}
// estrategia: dashboard -> "Nuevo" -> "Factura" (form EE vacio: inventario UX)
await page.goto(BASE + "/odoo/accounting", { waitUntil: "domcontentloaded" });
await page.waitForTimeout(5000);
const nuevo = page.locator('button:has-text("Nuevo")');
console.log("btn Nuevo:", await nuevo.count());
if (await nuevo.count()) {
  await nuevo.first().click();
  await page.waitForTimeout(2500);
  const items = await page.evaluate(() =>
    [...document.querySelectorAll(".o_dropdown_menu a, .dropdown-menu a, .o_menu_secondary a")].map((a) => a.textContent.trim()));
  console.log("ITEMS NUEVO:", JSON.stringify(items));
  const target = page.locator('.o_dropdown-menu a, .dropdown-menu a').filter({ hasText: /Factura/ }).first();
  if (await target.count()) { await target.click().catch(() => {}); await page.waitForTimeout(8000); }
}
console.log("TRAS FACTURA NUEVA:", page.url());
await page.screenshot({ path: OUT + "03-formulario.png" });

// fallback: form de contacto si no abrio form de factura
const tieneForm = await page.evaluate(() => document.querySelectorAll(".o_form_label").length);
console.log("labels en pantalla:", tieneForm);
if (!tieneForm) {
  await page.goto(BASE + "/odoo", { waitUntil: "domcontentloaded" }).catch(() => {});
  await page.waitForTimeout(3000);
  const contactos = page.getByText("Contactos", { exact: true });
  if (await contactos.count()) { await contactos.first().click().catch(() => {}); await page.waitForTimeout(6000); }
  const fila = page.locator(".o_data_row").first();
  if (await fila.count()) { await fila.click({ force: true }).catch(() => {}); await page.waitForTimeout(7000); }
  console.log("TRAS CONTACTO:", page.url());
  await page.screenshot({ path: OUT + "04-form-contacto-ee.png" });
}

const ux = await page.evaluate(() => ({
  url: location.href,
  botones_form: [...document.querySelectorAll(".o_form_button_save, .o_form_button_cancel, button.btn-primary, .o_form_button_draft")].map((b) => b.textContent.trim()).filter(Boolean).slice(0, 10),
  botones_box: [...document.querySelectorAll(".o_button_box button")].map((b) => b.title || b.textContent.trim()).slice(0, 8),
  statusbar: [...document.querySelectorAll(".o_statusbar_status button, .o_statusbar_status span")].map((b) => b.textContent.trim()).slice(0, 6),
  labels: [...document.querySelectorAll(".o_form_label")].map((l) => l.textContent.trim()).slice(0, 16),
  pestañas: [...document.querySelectorAll(".o_notebook .nav-link")].map((t) => t.textContent.trim()).slice(0, 8),
}));
console.log("UX:", JSON.stringify(ux, null, 1));
console.log("PAGEERRORS:", errs.length ? errs : "(ninguno)");
await browser.close();
