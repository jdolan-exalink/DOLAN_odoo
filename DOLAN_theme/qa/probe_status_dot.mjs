import { chromium } from "playwright";
const BASE = process.env.BASE || "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 860 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 160)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: process.env.PASS || "admin123" } },
});
await page.goto(`${BASE}/odoo`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".o_dolan_ai_btn", { timeout: 30000 });
await page.click(".o_dolan_ai_btn");
await page.waitForSelector(".o_dolan_ai_win", { timeout: 15000 });
await page.waitForTimeout(2500); // deja terminar checkStatus()

const info = await page.evaluate(() => {
  const dot = document.querySelector(".o_dolan_ai_status_dot");
  if (!dot) return { present: false };
  const cs = getComputedStyle(dot);
  const r = dot.getBoundingClientRect();
  return {
    present: true,
    className: dot.className,
    title: dot.title,
    rect: { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, x: Math.round(r.x), y: Math.round(r.y) },
    display: cs.display,
    background: cs.backgroundColor,
    visible: !!(r.width && r.height),
  };
});
const st = await page.request.post(`${BASE}/dolan_ai/status`, {
  data: { jsonrpc: "2.0", method: "call", params: {} },
}).then(r => r.json()).then(j => j.result || j.error);

console.log("DOT:", JSON.stringify(info));
console.log("STATUS RPC:", JSON.stringify(st));
console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 5)) : "(sin errores)");
await page.screenshot({ path: new URL("./shots/status-dot.png", import.meta.url).pathname });
await browser.close();
