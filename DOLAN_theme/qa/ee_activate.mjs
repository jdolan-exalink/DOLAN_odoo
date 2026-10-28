import { chromium } from "playwright";
const USER = process.env.EE_USER, PASS = process.env.EE_PASS;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
await page.goto("https://exalink.odoo.com/web/login", { waitUntil: "domcontentloaded", timeout: 60000 });
await page.fill('#login, input[name="login"]', USER);
await page.fill('#password, input[name="password"]', PASS);
await Promise.all([page.waitForNavigation({ timeout: 60000 }).catch(() => {}), page.click('button[type="submit"], .oe_login_button')]);
await page.waitForTimeout(7000);
const target = ["Helpdesk", "Planning", "Approvals", "Quality"];
for (const k of target) {
  const card = page.locator(".o_kanban_record, .o_module", { hasText: new RegExp(k, "i") }).first();
  if (!(await card.count().catch(() => 0))) { console.log("NO_CARD", k); continue; }
  const activate = card.locator("button", { hasText: /Activar|Activate/i }).first();
  if (await activate.count().catch(() => 0)) {
    try {
      await activate.click({ timeout: 6000 });
      await page.waitForTimeout(12000);
      console.log("ACTIVADO", k, "|", (await page.evaluate(() => document.title.slice(0, 40))));
    } catch (e) { console.log("FAIL_ACTIVATE", k, String(e).slice(0, 70)); }
  } else {
    console.log("SIN_BOTON", k, "| texto:", (await card.textContent()).slice(0, 80));
  }
  await page.goto("https://exalink.odoo.com/odoo/apps", { waitUntil: "domcontentloaded" }).catch(() => {});
  await page.waitForTimeout(6000);
}
await browser.close();
