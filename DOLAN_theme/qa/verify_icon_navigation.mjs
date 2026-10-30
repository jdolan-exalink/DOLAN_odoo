import { chromium } from "playwright";

// QA L45: cada icono de la grilla /dolan_apps debe abrir SU app, sin que el
// servicio "app por defecto" de dolan_ui lo secuestre hacia action-817
// (Operaciones). Se espera 5s por icono para atrapar la carrera tardía.
const BASE = process.env.BASE || "http://localhost:8070";
const results = [];
const check = (name, ok, detail) => results.push({ name, ok, detail });

// [nombre visible en la grilla, destino esperado (pathname o prefijo)]
const CASES = [
  ["DOLAN AI", "/dolan_ai"],
  ["Alquileres", "/dolan_alquileres"],
  ["Inicio", "/dolan_apps"],
  ["Taller", "/odoo/action-1205"],
  ["Facturación", "/odoo/customer-invoices"],
  ["Declaración Fiscal", "/odoo/action-1204"],
  ["Compras", "/odoo/purchase"],
];

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 } });
const page = await ctx.newPage();
const errs = [];
page.on("pageerror", (e) => errs.push("PAGEERR " + e.message.slice(0, 160)));
page.on("console", (m) => { if (m.type() === "error") errs.push("CONSOLE " + m.text().slice(0, 160)); });
await ctx.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: process.env.PASS || "admin123" } },
});

for (const [label, expected] of CASES) {
  await page.goto(`${BASE}/dolan_apps`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => document.querySelectorAll(".o_dolan_home_app").length > 0);
  const icon = page.locator(`.o_dolan_home_app:has-text("${label}")`).first();
  const href = await icon.getAttribute("href");
  await icon.click();
  await page.waitForTimeout(5000);
  const final = await page.evaluate(() => location.pathname);
  check(`icono "${label}" -> ${expected}`, final === expected,
    `href=${href} final=${final}${final !== expected ? " (esperado " + expected + ")" : ""}`);
}

// Entrada estándar Odoo (decisión S7): 1ª visita de la sesión = primera app del
// orden (Inicio → /dolan_apps); vuelta a /odoo = última app usada.
await page.goto(`${BASE}/odoo`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(5000);
const firstVisit = await page.evaluate(() => location.pathname);
check("1ª visita de sesión: primera app del orden (grilla Inicio)", firstVisit === "/dolan_apps",
  `pathname=${firstVisit}`);

// Odoo 20 solo restaura el menú guardado cuando la URL trae una acción; en
// una entrada limpia (/odoo sin ruta) abre SIEMPRE la primera app del orden.
await page.goto(`${BASE}/odoo/action-817`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(5000);
await page.click(".o_navbar_apps_menu button");
await page.waitForTimeout(700);
await page.locator(".o-dropdown--menu:has(.o_app) .o_app", { hasText: "Compras" }).first().click();
await page.waitForTimeout(4000);
const afterMenuClick = await page.evaluate(() => ({ path: location.pathname, stored: sessionStorage.getItem("menu_id") }));
await page.goto(`${BASE}/odoo`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(5000);
const back = await page.evaluate(() => location.pathname);
check("entrada limpia repetida: siempre la primera app (determinista)", back === "/dolan_apps",
  `menu_id=${afterMenuClick.stored} tras click=${afterMenuClick.path} -> entrada=${back}`);

await browser.close();
const seen = [...new Set(errs)];
check("sin errores JS", seen.length === 0, JSON.stringify(seen.slice(0, 4)));

let failed = 0;
for (const r of results) { if (!r.ok) failed++; console.log(`${r.ok ? "PASS" : "FAIL"} | ${r.name} | ${r.detail}`); }
console.log(`\n${results.length - failed}/${results.length} checks OK`);
process.exit(failed ? 1 : 0);
