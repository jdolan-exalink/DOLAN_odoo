import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage();
const errs = [];
page.on("console", (m) => errs.push(`[${m.type()}] ${m.text().slice(0, 160)}`));
page.on("response", async (r) => {
  if (r.url().includes("/dolan_ai/")) {
    try { const j = await r.json(); console.log("RESP", r.url().replace(BASE, ""), "->", JSON.stringify(j).slice(0, 300)); }
    catch { console.log("RESP", r.url().replace(BASE, ""), "->", r.status()); }
  }
});
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/dolan_ai`, { waitUntil: "domcontentloaded" });
await page.click("#dolan-ai-connect");
await page.waitForTimeout(9000);
console.log("STATUS_TEXT:", (await page.locator("#dolan-ai-status").textContent()).trim());
console.log("CONSOLE:", JSON.stringify(errs.slice(0, 6)));
await browser.close();
