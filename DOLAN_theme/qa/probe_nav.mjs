import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".o_dolan_dash", { timeout: 25000 });
for (const t of [0, 1500, 3500]) {
  await page.waitForTimeout(t === 0 ? 100 : 2000);
  const p = await page.evaluate(() => ({
    rail: document.querySelectorAll(".o_dolan_rail_item").length,
    sections: [...document.querySelectorAll(".o_menu_sections")].map((n) => n.textContent.trim().slice(0, 60)),
    navText: document.querySelector(".o_main_navbar")?.textContent.replace(/\s+/g, " ").slice(0, 140),
    hash: location.hash.slice(0, 80),
  }));
  console.log(`t+${t}:`, JSON.stringify(p));
}
await browser.close();
