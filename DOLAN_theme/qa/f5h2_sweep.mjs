import { chromium } from "playwright";
import fs from "node:fs";
const BASE = "http://localhost:8070";
const SHOTS = "/root/DOLAN_odoo20/DOLAN_theme/qa/shots/f5h2";
fs.mkdirSync(SHOTS, { recursive: true });
const apps = JSON.parse(fs.readFileSync("/root/DOLAN_odoo20/rea/apps.json", "utf8"));

async function session(browser, user, pass, tema) {
  const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
  const errs = [];
  page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 100)); });
  await page.request.post(`${BASE}/web/session/authenticate`, {
    data: { jsonrpc: "2.0", params: { db: "dolan", login: user, password: pass } },
  });
  // forzar tema vía config (el server la aplica por usuario)
  await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);
  const temaReal = await page.evaluate(() => document.documentElement.dataset.dolanTheme || "light");
  return { page, errs, temaReal };
}

const browser = await chromium.launch();
// S1: juan en OSCURO
const juan = await session(browser, "juan@dolan.com.ar", "admin123", "dark");
console.log("juan tema:", juan.temaReal);
// S2: operador CLARO
const op = await session(browser, "operador@dolan.com.ar", "operador123", "light");
console.log("operador tema:", op.temaReal);

const results = {};
for (const [mod, info] of Object.entries(apps)) {
  results[mod] = { root: info.root };
  for (const [who, s] of [["dark_juan", juan], ["operador", op]]) {
    s.errs.length = 0;
    let resp = null;
    try {
      if (info.root) {
        const sel = `[data-menu-xmlid="${info.root}"]`;
        if (!(await s.page.locator(sel).count())) {
          await s.page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded", timeout: 45000 });
          await s.page.waitForTimeout(3000);
        }
        try {
          await s.page.locator(sel).first().click({ timeout: 8000 });
        } catch (e1) {
          // reintento: volver a home y click de nuevo (el rail se recarga tras navegaciones)
          await s.page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded", timeout: 45000 });
          await s.page.waitForTimeout(3500);
          await s.page.locator(sel).first().click({ timeout: 8000 });
        }
        resp = { status: () => 200 };
      } else {
        const target = info.kind === "url" ? BASE + info.value : `${BASE}/odoo/action-${info.value}`;
        resp = await s.page.goto(target, { waitUntil: "domcontentloaded", timeout: 45000 });
      }
      await s.page.waitForTimeout(3500);
      const render = await s.page.evaluate(() => ({
        view: !!document.querySelector(".o_view_controller, .o_action, .o_client_action"),
        filas: document.querySelectorAll(".o_data_row, .o_kanban_record, .o_graph_svg, .o_calendar_container, .o_kanban_view").length,
      }));
      if (who === "dark_juan") await s.page.screenshot({ path: `${SHOTS}/${mod}-dark.png` });
      else await s.page.screenshot({ path: `${SHOTS}/${mod}-op.png` });
      results[mod][who] = {
        status: resp ? resp.status() : 0, render: render.view, el: render.filas,
        errores: [...new Set(s.errs)].slice(0, 2),
      };
    } catch (e) {
      results[mod][who] = { status: 0, error: String(e).slice(0, 80), errores: [...new Set(s.errs)].slice(0, 2) };
    }
  }
  console.log("APP", mod, "dark:", JSON.stringify(results[mod].dark_juan), "op:", JSON.stringify(results[mod].operador));
}
fs.writeFileSync("/root/DOLAN_odoo20/rea/f5h2.json", JSON.stringify(results, null, 1));
const bad = Object.entries(results).filter(([, r]) =>
  (r.dark_juan && (r.dark_juan.errores?.length || !r.dark_juan.render)) ||
  (r.operador && (r.operador.errores?.length || !r.operador.render))).map(([m, r]) => m);
console.log("RESUMEN apps con problemas:", JSON.stringify(bad));
await browser.close();
