import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage();
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
let dump = null;
page.on("response", async (res) => {
  if (res.url().includes("load_menus")) {
    try { dump = await res.json(); } catch {}
  }
});
await page.goto(`${BASE}/web`, { waitUntil: "networkidle" }).catch(() => {});
await page.waitForTimeout(4000);
if (!dump) { console.log("NO load_menus capturado"); await browser.close(); process.exit(0); }
const res = dump.result || {};
const keys = Object.keys(res);
console.log("total claves:", keys.length);
console.log("claves tipo:", keys.length ? typeof res[keys[0]] : "-");
for (const k of ["fleet.menu_root", "mrp.mrp_menu_root", "point_of_sale.menu_point_root", "stock.menu_stock_root"]) {
  console.log(k, "->", res[k] ? JSON.stringify(res[k]).slice(0, 200) : "AUSENTE");
}
const appsKey = res.apps;
console.log("apps presente:", !!appsKey, "| tipo:", Array.isArray(appsKey) ? "array" : typeof appsKey);
if (Array.isArray(appsKey)) console.log("apps:", JSON.stringify(appsKey).slice(0, 600));
await browser.close();
