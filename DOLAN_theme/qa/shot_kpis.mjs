import { chromium } from "playwright";
import { mkdirSync } from "fs";
const BASE = "http://localhost:8070";
mkdirSync(new URL("./shots/", import.meta.url).pathname, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
page.on("pageerror", (e) => errs.push(String(e).slice(0, 300)));
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
try { await page.waitForSelector(".o_dolan_dash", { timeout: 25000 }); }
catch { console.log("KPI dashboard no aparecio (probando click en Tablero)"); 
  try { await page.getByRole("link", { name: "Tablero" }).first().click(); await page.waitForSelector(".o_dolan_dash", { timeout: 15000 }); } catch { console.log("sin tablero"); } }
await page.waitForTimeout(1500);
const cards = await page.evaluate(() => [...document.querySelectorAll(".dolan_card")].map(c => c.textContent.replace(/\s+/g, " ").trim().slice(0, 90)));
console.log("CARDS:", JSON.stringify(cards, null, 1));
console.log("CONSOLE:", errs.length ? errs : "(sin errores)");
await page.screenshot({ path: new URL("./shots/kpis.png", import.meta.url).pathname });
console.log("SHOT ok");
await browser.close();
