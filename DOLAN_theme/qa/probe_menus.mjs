import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 150)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".o_dolan_dash", { timeout: 25000 });
await page.waitForTimeout(1500);
const probe = await page.evaluate(() => {
  const sec = [...document.querySelectorAll(".o_menu_sections")].map((n) => n.textContent.trim());
  const anywhere = document.body.innerHTML.includes("Listados");
  const tabs = [...document.querySelectorAll(".o_menu_sections a, .o_menu_sections button")].map((e) => `${e.tagName}:${e.textContent.trim()}`);
  return { sec, anywhere, tabs };
});
console.log("PROBE:", JSON.stringify(probe, null, 1));
console.log("ERR:", errs.slice(0, 3));
await browser.close();
