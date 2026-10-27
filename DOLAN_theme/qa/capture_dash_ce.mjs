import { chromium } from "playwright";
const BASE = "http://localhost:8070";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const errs = [];
page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 140)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector("[data-menu-xmlid]", { timeout: 25000 });
await page.waitForTimeout(2500);

const apps = await page.evaluate(() =>
  [...document.querySelectorAll("[data-menu-xmlid]")].map((e) => ({
    xmlid: e.getAttribute("data-menu-xmlid"),
    label: (e.getAttribute("title") || e.textContent || "").trim().slice(0, 40),
  }))
);
console.log("APPS:", JSON.stringify(apps, null, 0));

const targets = [
  ["inventario", ["Inventor"]],
  ["compras", ["Compra"]],
  ["contabilidad", ["Contab", "Factur"]],
  ["empleados", ["Emplead"]],
  ["productos", ["Product"]],
  ["flotilla", ["Flotill", "Flota"]],
  ["mantenimiento", ["Mantenimiento"]],
];
for (const [slug, keys] of targets) {
  const hit = apps.find((a) => keys.some((k) => a.label.includes(k)));
  if (!hit) { console.log(`SIN APP: ${slug} (${keys.join("/")})`); continue; }
  const sel = `.o_dolan_rail_item[data-menu-xmlid="${hit.xmlid}"], [data-menu-xmlid="${hit.xmlid}"]`;
  try {
    await page.locator(sel).first().click({ timeout: 8000 });
    await page.waitForTimeout(5500);
    const titulo = await page.evaluate(() => document.title.slice(0, 60));
    await page.screenshot({ path: `shots/dash/${slug}.png` });
    console.log(`OK ${slug} <- ${hit.xmlid} | ${titulo}`);
  } catch (e) { console.log(`FAIL ${slug}: ${String(e).slice(0, 120)}`); }
}
console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 6)) : "(sin errores)");
await browser.close();
