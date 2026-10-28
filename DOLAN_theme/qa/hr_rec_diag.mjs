import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("pageerror", (e) => errs.push("PAGEERROR " + String(e).slice(0, 600)));
page.on("console", (m) => { if (m.type() === "error") errs.push("CONSOLE " + m.text().slice(0, 500)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(4000);
await page.locator('[data-menu-xmlid="hr_recruitment.menu_hr_recruitment_root"]').first().click();
await page.waitForTimeout(6000);
// abrir Configuración dentro de la app (donde está el SettingsPage)
const cfg = page.locator(".o_navbar .o_nav_entry, [class*=menu_sections] a, .o_menu_sections a").filter({ hasText: /Configuraci/i }).first();
if (await cfg.count()) {
  await cfg.click();
  await page.waitForTimeout(6000);
}
console.log("URL:", page.url().slice(0, 80));
for (const e of errs) console.log("ERR>", e);
await page.screenshot({ path: "/root/DOLAN_odoo20/DOLAN_theme/qa/shots/l37-hrrec-config.png" });
await browser.close();
