import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
page.on("pageerror", (e) => { console.log("PAGEERROR:"); console.log(String(e.stack || e).slice(0, 1200)); });
page.on("console", (m) => { if (m.type() === "error") console.log("CONSOLE:", m.text().slice(0, 800), "\n---"); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(4000);
await page.locator('[data-menu-xmlid="hr_recruitment.menu_hr_recruitment_root"]').first().click();
await page.waitForTimeout(8000);
console.log("DONE");
await browser.close();
