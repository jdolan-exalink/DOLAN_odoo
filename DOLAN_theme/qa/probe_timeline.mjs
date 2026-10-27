import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const warns = [];
page.on("console", (m) => { if (["error","warning"].includes(m.type())) warns.push(`[${m.type()}] ${m.text().slice(0,150)}`); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".o_dolan_dash", { timeout: 25000 });
await page.locator(".dolan_card", { hasText: "Compras por pagar" }).click();
for (const t of [0, 300, 900, 1500]) {
  await page.waitForTimeout(t === 0 ? 60 : 300);
  const s = await page.evaluate(() => ({
    actives: document.querySelectorAll(".dolan_block_active").length,
    first: document.querySelector(".dolan_detail_block")?.className,
    section: !!document.querySelector(".dolan_section"),
    cardOn: !!document.querySelector(".dolan_card.on"),
  }));
  console.log(`t+${t}ms`, JSON.stringify(s));
}
console.log("WARN:", warns.slice(0,4));
await browser.close();
