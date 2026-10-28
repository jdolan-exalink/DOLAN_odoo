import { chromium } from "playwright";
const USER = process.env.EE_USER, PASS = process.env.EE_PASS;
if (!USER || !PASS) { console.error("FALTAN EE_USER/EE_PASS"); process.exit(2); }
const OUT = "/root/DOLAN_odoo20/DOLAN_theme/docs/evidence/ee-demo/full";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 120)); });
await page.goto("https://exalink.odoo.com/web/login", { waitUntil: "domcontentloaded", timeout: 60000 });
await page.fill('#login, input[name="login"]', USER);
await page.fill('#password, input[name="password"]', PASS);
await Promise.all([page.waitForNavigation({ timeout: 60000 }).catch(() => {}), page.click('button[type="submit"], .oe_login_button')]);
await page.waitForTimeout(6000);
console.log("LOGIN url:", page.url());
// home = grilla de apps EE
await page.goto("https://exalink.odoo.com/odoo", { waitUntil: "domcontentloaded" }).catch(() => {});
await page.waitForTimeout(7000);
const tiles = await page.evaluate(() =>
  [...document.querySelectorAll(".o_app, [class*=o_app]")].map((e) => ({
    name: (e.querySelector(".o_app_name, .o_name, [class*=name]")?.textContent || e.textContent || "").trim().slice(0, 40),
  })).filter((t) => t.name)
);
console.log("GRILLA:", JSON.stringify(tiles.map((t) => t.name)));
await page.screenshot({ path: `${OUT}/00-grilla-apps.png` });
// apps EE-only clave (paridad con lo que construimos + gaps)
const KEY = ["Suscripciones", "Alquiler", "IA", "Taller", "Código de barras", "Manufactura", "Ventas", "Contabilidad"];
const clicked = [];
for (const k of KEY) {
  const t = page.locator(".o_app", { hasText: new RegExp(`^${k}`, "i") }).first();
  if (!(await t.count().catch(() => 0))) { console.log("SIN_APP", k); continue; }
  try {
    await t.click({ timeout: 8000 });
    await page.waitForTimeout(6000);
    const title = await page.evaluate(() => document.title.slice(0, 60));
    await page.screenshot({ path: `${OUT}/${k.toLowerCase().replace(/\s+/g, "-")}.png` });
    clicked.push(k);
    console.log("CAPTURADA", k, "|", title);
    await page.goto("https://exalink.odoo.com/odoo", { waitUntil: "domcontentloaded" }).catch(() => {});
    await page.waitForTimeout(5000);
  } catch (e) { console.log("FAIL", k, String(e).slice(0, 70)); }
}
console.log("TOTAL capturadas:", clicked.length, "| errores consola:", errs.length ? [...new Set(errs)].slice(0, 3) : 0);
await browser.close();
