import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 860 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 140)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
const resp = await page.goto(`${BASE}/dolan_ai`, { waitUntil: "domcontentloaded" });
console.log("PAGE status:", resp.status());
if (resp.status() !== 200) { console.log("BODY:", (await resp.text()).slice(0, 200)); await browser.close(); process.exit(1); }
console.log("H3:", await page.locator("h3").first().textContent());
await page.screenshot({ path: "/root/odoo20/DOLAN_ai/qa/shots/dolan-ai-page.png" });
// iniciar device flow REAL (auth.openai.com)
await page.click("#dolan-ai-connect");
await page.waitForSelector("#dolan-ai-device", { state: "visible", timeout: 45000 });
await page.waitForTimeout(1200);
const code = (await page.locator("#dolan-ai-code").textContent()).trim();
const uri = (await page.locator("#dolan-ai-uri").textContent()).trim();
const st = (await page.locator("#dolan-ai-status").textContent()).trim();
console.log("DEVICE code:", code, "| uri:", uri, "| status:", st);
await page.screenshot({ path: "/root/odoo20/DOLAN_ai/qa/shots/dolan-ai-device.png" });
console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 4)) : "(sin errores)");
await browser.close();
