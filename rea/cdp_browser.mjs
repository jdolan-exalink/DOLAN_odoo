/** Chromium persistent con CDP :9222 logueado a Odoo (para REA). */
import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch({ args: ["--remote-debugging-port=9222", "--remote-debugging-address=127.0.0.1"] });
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(6000);
console.log("CDP_READY", (await browser.contexts()[0].pages()[0].title?.()) || "ok");
setInterval(() => {}, 1 << 30); // mantener vivo
