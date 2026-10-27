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
await page.waitForTimeout(1800);
const st = await page.evaluate(() => ({
  theme: document.documentElement.dataset.dolanTheme,
  density: document.documentElement.dataset.dolanDensity,
  bg: getComputedStyle(document.body).backgroundColor,
}));
console.log("THEME:", JSON.stringify(st));
await page.screenshot({ path: "shots/dark-compact.png" });
console.log("CONSOLE:", errs.length ? errs : "(sin errores)");
await browser.close();
