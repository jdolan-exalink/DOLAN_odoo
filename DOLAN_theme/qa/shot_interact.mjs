import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
page.on("pageerror", (e) => errs.push(String(e).slice(0, 300)));
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".o_dolan_dash", { timeout: 25000 });

// 1) click en la tarjeta "Compras por pagar" -> seccion con grafico
await page.locator(".dolan_card", { hasText: "Compras por pagar" }).click();
await page.waitForSelector(".dolan_section .dolan_bars", { timeout: 15000 });
await page.waitForTimeout(900);
const chart = await page.evaluate(() => ({
  titulo: document.querySelector(".dolan_section_title")?.textContent,
  barras: document.querySelectorAll(".dolan_bar").length,
  bloqueActivo: document.querySelectorAll(".dolan_block_active").length,
  botonPagar: document.querySelectorAll(".dolan_pay_btn").length,
}));
console.log("SECCION:", JSON.stringify(chart));
await page.screenshot({ path: "shots/tablero-seccion.png" });

// 2) toggle de sidebar compacta
await page.locator("[data-dolan-rail-toggle]").click();
await page.waitForTimeout(600);
const compact = await page.evaluate(() => ({
  railCompact: document.querySelector(".o_dolan_rail")?.classList.contains("o_dolan_rail_compact"),
  bodyCompact: document.body.classList.contains("dolan-compact"),
  ancho: document.querySelector(".o_dolan_rail")?.getBoundingClientRect().width,
}));
console.log("COMPACT:", JSON.stringify(compact));
await page.screenshot({ path: "shots/sidebar-compacta.png" });

console.log("CONSOLE:", errs.length ? errs : "(sin errores)");
await browser.close();
