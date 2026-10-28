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
// app IA (tile con texto IA)
const tile = page.locator(".o_app", { hasText: /^IA/ }).first();
if (!(await tile.count())) { console.log("SIN_APP IA"); await browser.close(); process.exit(1); }
await tile.click();
await page.waitForTimeout(7000);
const cards = await page.evaluate(() => [...document.querySelectorAll(".o_kanban_record, .o_card_record")].map(e => ({
  nombre: (e.querySelector("b, strong, h3, [class*=name]")?.textContent || e.textContent || "").trim().slice(0, 40),
  chips: [...e.querySelectorAll(".badge, .o_tag, [class*=chip]")].map(c => c.textContent.trim().slice(0, 24)).slice(0, 8),
})));
console.log("AGENTES EE:", JSON.stringify(cards).slice(0, 700));
await page.screenshot({ path: `${OUT}/ia-agentes-grid.png` });
// abrir el primer agente (Odoo AI) y capturar su form/chat
const first = page.locator(".o_kanban_record, .o_card_record").first();
if (await first.count()) {
  await first.click();
  await page.waitForTimeout(7000);
  const form = await page.evaluate(() => {
    const tabs = [...document.querySelectorAll(".nav-link, [role=tab]")].map(t => t.textContent.trim().slice(0, 24)).slice(0, 8);
    const fields = [...document.querySelectorAll("label")].map(l => l.textContent.trim().slice(0, 30)).filter(Boolean).slice(0, 14);
    const buttons = [...document.querySelectorAll("button")].map(b => b.textContent.trim().slice(0, 22)).filter(Boolean).slice(0, 14);
    return { tabs, fields, buttons };
  });
  console.log("FORM AGENTE:", JSON.stringify(form).slice(0, 700));
  await page.screenshot({ path: `${OUT}/ia-agente-form.png` });
}
console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 2)) : 0);
await browser.close();
