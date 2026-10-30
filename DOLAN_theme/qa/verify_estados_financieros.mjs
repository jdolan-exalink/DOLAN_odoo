import { chromium } from "playwright";

// QA L50 (S8/C10 · opción B): estados financieros propios en XLSX bajo
// Contabilidad > Reportes > Estados financieros.
// L51 (S8/C11): incluye la Auditoría de diario propia (Revisión > Control).
const BASE = process.env.BASE || "http://localhost:8070";
const PASS = process.env.PASS || "admin123";
const results = [];
const check = (name, ok, detail) => results.push({ name, ok, detail });

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 }, acceptDownloads: true });
const page = await ctx.newPage();
const errs = [];
page.on("pageerror", (e) => errs.push("PAGEERR " + e.message.slice(0, 200)));
page.on("console", (m) => { if (m.type() === "error") errs.push("CONSOLE " + m.text().slice(0, 200)); });
await ctx.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: PASS } },
});

// 1) localizar las acciones de los 3 reportes en load_menus
const menus = await (await ctx.request.get(`${BASE}/web/webclient/load_menus`)).json();
const wanted = {
  "Balance general": null,
  "Estado de resultados": null,
  "Flujo de efectivo": null,
  "Auditoría de diario": null,
};
for (const key of Object.keys(menus)) {
  const m = menus[key];
  if (m && m.name && Object.prototype.hasOwnProperty.call(wanted, m.name)) wanted[m.name] = m.actionID;
}
check("menús de estados financieros en Contabilidad > Reportes",
  Object.values(wanted).every(Boolean), JSON.stringify(wanted));

// 2) abrir cada wizard y generar el XLSX
for (const [name, actionId] of Object.entries(wanted)) {
  if (!actionId) continue;
  await page.goto(`${BASE}/odoo/action-${actionId}`, { waitUntil: "domcontentloaded" });
  const modal = page.locator(".modal .o_form_view").first();
  try {
    await modal.waitFor({ state: "visible", timeout: 20000 });
  } catch {
    check(`wizard "${name}" abre`, false, "modal no visible");
    continue;
  }
  check(`wizard "${name}" abre`, true, "modal visible");
  const dialog = page.locator(".modal").last();
  const [download] = await Promise.all([
    page.waitForEvent("download", { timeout: 30000 }),
    dialog.locator("button", { hasText: "Generar XLSX" }).click(),
  ]);
  const path = await download.path();
  const fs = await import("node:fs");
  const buf = fs.readFileSync(path);
  const isZip = buf[0] === 0x50 && buf[1] === 0x4b; // magic PK del xlsx (zip)
  check(`XLSX de "${name}" se genera`, isZip && buf.length > 1024,
    `${download.suggestedFilename()} ${buf.length} bytes, zip=${isZip}`);
}

console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 5)) : "(sin errores)");
check("0 errores JS", errs.length === 0, `${errs.length}`);
await browser.close();

let failed = 0;
for (const r of results) { if (!r.ok) failed++; console.log(`${r.ok ? "PASS" : "FAIL"} | ${r.name} | ${r.detail}`); }
console.log(`\n${results.length - failed}/${results.length} checks OK`);
process.exit(failed ? 1 : 0);
