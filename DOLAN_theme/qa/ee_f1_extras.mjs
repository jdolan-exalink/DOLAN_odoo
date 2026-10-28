import { chromium } from "playwright";
const USER = process.env.EE_USER, PASS = process.env.EE_PASS;
const OUT = "/root/DOLAN_odoo20/DOLAN_theme/docs/evidence/ee-demo/full";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
await page.goto("https://exalink.odoo.com/web/login", { waitUntil: "domcontentloaded", timeout: 60000 });
await page.fill('#login, input[name="login"]', USER);
await page.fill('#password, input[name="password"]', PASS);
await Promise.all([page.waitForNavigation({ timeout: 60000 }).catch(() => {}), page.click('button[type="submit"], .oe_login_button')]);
await page.waitForTimeout(7000);
// grilla actual (con las nuevas apps habilitadas)
await page.goto("https://exalink.odoo.com/odoo", { waitUntil: "domcontentloaded" }).catch(() => {});
await page.waitForTimeout(7000);
const tiles = await page.evaluate(() => [...document.querySelectorAll(".o_app")].map(e => (e.querySelector("[class*=name]")?.textContent || e.textContent || "").trim().slice(0, 30)).filter(Boolean));
console.log("GRILLA:", JSON.stringify(tiles));
const KEY = ["Ayuda", "Planificación", "Aprobaciones", "Calidad", "Empleados"];
for (const k of KEY) {
  const t = page.locator(".o_app", { hasText: new RegExp(`^${k}`, "i") }).first();
  if (!(await t.count().catch(() => 0))) { console.log("SIN_APP", k); continue; }
  try {
    await t.click({ timeout: 8000 });
    await page.waitForTimeout(6000);
    console.log("CAPTURADA", k, "|", (await page.evaluate(() => document.title.slice(0, 50))));
    await page.screenshot({ path: `${OUT}/${k.toLowerCase()}.png` });
    await page.goto("https://exalink.odoo.com/odoo", { waitUntil: "domcontentloaded" }).catch(() => {});
    await page.waitForTimeout(5000);
  } catch (e) { console.log("FAIL", k, String(e).slice(0, 60)); }
}
await browser.close();
