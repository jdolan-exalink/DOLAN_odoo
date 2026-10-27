import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0,150)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".o_dolan_dash", { timeout: 25000 });
const box = await page.evaluate(() => {
  const b = document.querySelector(".dolan_pay_btn");
  if (!b) return { existe: false };
  const r = b.getBoundingClientRect();
  const visible = r.width > 0 && r.right <= window.innerWidth && r.bottom <= window.innerHeight + 50;
  return { existe: true, visible, right: Math.round(r.right), ancho: Math.round(r.width), viewport: window.innerWidth };
});
console.log("PAY_BTN:", JSON.stringify(box));
await page.screenshot({ path: "shots/tablero-final.png" });
console.log("CONSOLE:", errs.length ? errs : "(sin errores)");
await browser.close();
