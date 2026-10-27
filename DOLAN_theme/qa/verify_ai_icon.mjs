import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 120)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector("[data-menu-xmlid]", { timeout: 25000 });
await page.waitForTimeout(2500);
const rail = await page.evaluate(() => {
  const it = [...document.querySelectorAll("[data-menu-xmlid]")].find((e) => e.getAttribute("data-menu-xmlid") === "DOLAN_ai.menu_dolan_ai_root");
  if (!it) return null;
  const img = it.querySelector("img");
  return { label: it.textContent.trim().slice(0, 16), img: img ? img.getAttribute("src").slice(0, 48) : null };
});
console.log("RAIL:", JSON.stringify(rail));
await page.locator('[data-menu-xmlid="base.menu_management"]').first().click();
await page.waitForTimeout(4000);
const mod = await page.evaluate(() => {
  const cards = [...document.querySelectorAll(".o_module, .o_kanban_record, [class*=module]")];
  const c = cards.find((e) => (e.textContent || "").includes("DOLAN AI"));
  if (!c) return null;
  const img = c.querySelector("img");
  return { text: c.textContent.trim().slice(0, 40), icon: img ? (img.getAttribute("src") || "").slice(0, 48) : null };
});
console.log("MODULO:", JSON.stringify(mod));
await page.screenshot({ path: "/root/DOLAN_odoo20/DOLAN_ai/qa/shots/dolan-ai-app-tile.png" });
console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 4)) : "(sin errores)");
await browser.close();
