import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const warns = [];
page.on("console", (m) => { if (["error","warning"].includes(m.type())) warns.push(`[${m.type()}] ${m.text().slice(0,180)}`); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".o_dolan_dash", { timeout: 25000 });
await page.locator(".dolan_card", { hasText: "Compras por pagar" }).click();
await page.waitForSelector(".dolan_section", { timeout: 15000 });
await page.waitForTimeout(500);
const probe = await page.evaluate(() => {
  const blocks = [...document.querySelectorAll(".dolan_detail_block")];
  return {
    nBlocks: blocks.length,
    classes: blocks.map((b) => b.className),
    seccionCard: document.querySelector(".dolan_card.on")?.textContent.slice(0, 30),
  };
});
console.log("PROBE:", JSON.stringify(probe, null, 1));
console.log("WARN:", warns.slice(0, 5));
await browser.close();
