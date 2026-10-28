import { chromium } from "playwright";
import fs from "node:fs";
const BASE = "http://localhost:8070";
const SHOTS = "/root/DOLAN_odoo20/DOLAN_theme/qa/shots/analysis";
const apps = JSON.parse(fs.readFileSync("/root/DOLAN_odoo20/rea/apps.json", "utf8"));
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
const results = {};
let currentErrs = [];
page.on("console", (m) => { if (m.type() === "error") currentErrs.push(m.text().slice(0, 120)); });
await page.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: "admin123" } },
});
await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
await page.waitForSelector("[data-menu-xmlid]", { timeout: 25000 });
await page.waitForTimeout(2500);
const rail = new Set(await page.evaluate(() => [...document.querySelectorAll("[data-menu-xmlid]")].map((e) => e.getAttribute("data-menu-xmlid"))));
for (const [mod, info] of Object.entries(apps)) {
  currentErrs = [];
  const target = info.kind === "url" ? BASE + info.value : `${BASE}/odoo/action-${info.value}`;
  let landed = "";
  try {
    const resp = await page.goto(target, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(4200);
    landed = resp ? resp.url().replace(BASE, "") : "";
    const h = await page.evaluate(() => {
      const t = document.querySelector(".o_control_panel .o_cp_top_left, .o_control_panel") ||
                document.querySelector("h1, h2, .o_main_cellheader");
      const listRows = document.querySelectorAll(".o_data_row, .o_kanban_record, .o_list_table tbody tr").length;
      return { titulo: (t?.textContent || document.title).trim().slice(0, 60), registros: listRows };
    });
    await page.screenshot({ path: `${SHOTS}/${mod}.png` });
    results[mod] = {
      kind: info.kind, root: info.root, rail: info.root ? rail.has(info.root) : null,
      status: resp ? resp.status() : 0, landed: landed.slice(0, 70),
      titulo: h.titulo, registros: h.registros,
      errores_consola: [...new Set(currentErrs)].slice(0, 3),
    };
  } catch (e) {
    results[mod] = { kind: info.kind, root: info.root, rail: info.root ? rail.has(info.root) : null,
      status: 0, error: String(e).slice(0, 100), errores_consola: [...new Set(currentErrs)].slice(0, 3) };
  }
  console.log("MOD", mod, JSON.stringify({ ...results[mod], titulo: results[mod]?.titulo?.slice(0, 30) }).slice(0, 220));
}
fs.writeFileSync("/root/DOLAN_odoo20/rea/analysis_pw.json", JSON.stringify(results, null, 1));
const resumen = {
  apps: Object.keys(results).length,
  con_errores_consola: Object.values(results).filter((r) => (r.errores_consola || []).length).length,
  fuera_del_rail: Object.entries(results).filter(([, r]) => r.rail === false).map(([m]) => m),
  fallos: Object.entries(results).filter(([, r]) => !r.status || r.status >= 400 || r.error).map(([m, r]) => m),
};
console.log("RESUMEN:", JSON.stringify(resumen));
await browser.close();
