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
await page.waitForTimeout(1200);
const cards = await page.evaluate(() =>
  [...document.querySelectorAll(".dolan_card")].map((c) => c.querySelector(".dolan_icon")?.textContent.trim()));
console.log("WIDGETS:", JSON.stringify(cards));
await page.screenshot({ path: "shots/home-widgets.png" });

// atajo: g luego c -> Compras
await page.keyboard.press("g");
await page.waitForTimeout(200);
await page.keyboard.press("c");
await page.waitForTimeout(1800);
const nav = await page.evaluate(() => ({
  seccion: [...document.querySelectorAll(".o_menu_sections")].map((n) => n.textContent.trim()).slice(0, 2),
  railActive: document.querySelector(".o_dolan_rail_active .o_dolan_rail_label")?.textContent,
  hash: location.hash.slice(0, 60),
}));
console.log("HOTKEY g+c ->", JSON.stringify(nav));
await page.screenshot({ path: "shots/hotkey-compras.png" });

// badges en Listados
await page.getByText("Listados", { exact: true }).first().click();
await page.waitForTimeout(2000);
const badges = await page.evaluate(() => {
  const cells = [...document.querySelectorAll(".o_list_table .badge")];
  return { n: cells.length, ejemplos: cells.slice(0, 4).map((b) => b.textContent.trim()) };
});
console.log("BADGES:", JSON.stringify(badges));
await page.screenshot({ path: "shots/lista-badge.png" });

console.log("CONSOLE:", errs.length ? errs : "(sin errores)");
await browser.close();
