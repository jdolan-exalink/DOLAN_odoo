import { chromium } from "playwright";
const USER = process.env.EE_USER, PASS = process.env.EE_PASS;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
await page.goto("https://exalink.odoo.com/web/login", { waitUntil: "domcontentloaded", timeout: 60000 });
await page.fill('#login, input[name="login"]', USER);
await page.fill('#password, input[name="password"]', PASS);
await Promise.all([page.waitForNavigation({ timeout: 60000 }).catch(() => {}), page.click('button[type="submit"], .oe_login_button')]);
await page.waitForTimeout(7000);
// ir a Aplicaciones → quitar filtro → buscar "helpdesk"
await page.goto("https://exalink.odoo.com/odoo/apps", { waitUntil: "domcontentloaded" }).catch(() => {});
await page.waitForTimeout(8000);
const search = page.locator("input.o_searchbar_input, [name=search], input[type=search]").first();
if (await search.count()) {
  await search.fill("helpdesk");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(8000);
}
const res = await page.evaluate(() => {
  const cards = [...document.querySelectorAll(".o_kanban_record, .o_module")].slice(0, 6).map(c => c.textContent.trim().slice(0, 90));
  const err = document.body.textContent.includes("No se encontraron") || document.body.textContent.includes("No result");
  return { cards, empty: err };
});
console.log("SEARCH:", JSON.stringify(res).slice(0, 600));
await page.screenshot({ path: "/root/DOLAN_odoo20/DOLAN_theme/qa/shots/l37-ee-apps-helpdesk.png" });
await browser.close();
