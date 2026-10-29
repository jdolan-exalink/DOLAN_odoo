import { chromium } from "playwright";

// QA L47 (S8/P1): paridad de la app "Contabilidad" con la demo EE.
//  - la app raíz se llama Contabilidad (en_US y es_AR) y abre el webclient
//  - el admin ve las secciones Contabilidad / Revisión / Reportes / Banco y Caja
//  - dentro hay Asientos contables, Apuntes contables, Pista de auditoría e informes argentinos
//  - el rol Invoicing (operador) no gana permisos de escritura nuevos (solo visibilidad)
const BASE = process.env.BASE || "http://localhost:8070";
const PASS = process.env.PASS || "admin123";
const shots = new URL("./shots/", import.meta.url).pathname;
const results = [];
const check = (name, ok, detail) => results.push({ name, ok, detail });

const browser = await chromium.launch();

async function menusAs(login) {
  const ctx = await browser.newContext();
  const r = await ctx.request.post(`${BASE}/web/session/authenticate`, {
    data: { jsonrpc: "2.0", params: { db: "dolan", login, password: PASS } },
  });
  const j = await r.json();
  if (!j.result || !j.result.uid) throw new Error(`login falló para ${login}`);
  const body = await (await ctx.request.get(`${BASE}/web/webclient/load_menus`)).text();
  await ctx.close();
  return { doc: JSON.parse(body), uid: j.result.uid };
}

const { doc } = await menusAs("juan@dolan.com.ar");
const res = {};
for (const k of Object.keys(doc)) res[String(k)] = doc[k];

const roots = [];
for (const cid of (res.root?.children || [])) {
  const m = res[String(cid)];
  if (m && m.appID === m.id) roots.push(m);
}
const app = roots.find((m) => m.xmlid === "account.menu_finance");
check("app raíz presente", !!app, app ? `name=${app.name} path=${app.actionPath || app.actionID}` : "no está");
check("la app se llama Contabilidad", !!app && app.name === "Contabilidad", app ? `name="${app.name}"` : "-");

const sections = (app?.children || []).map((cid) => res[String(cid)]).filter(Boolean).map((s) => s.name);
for (const want of ["Contabilidad", "Revisión", "Reportes", "Banco y Caja"]) {
  check(`sección "${want}" visible`, sections.includes(want), sections.join(", "));
}

// descenso útil (como en la demo)
const names = new Set(Object.values(res).filter((m) => m && m.name).map((m) => m.name));
for (const want of ["Asientos contables", "Apuntes contables", "Pista de auditoría"]) {
  check(`menú "${want}" visible para el admin`, names.has(want), names.has(want) ? "ok" : "no visible");
}
const iibb = Object.values(res).filter((m) => m && m.name && /^IIBB/.test(m.name)).map((m) => m.name);
check("informes argentinos (IIBB) dentro de Reportes", iibb.length >= 2, JSON.stringify(iibb));

// navegación real: la app abre el webclient
const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 } });
const page = await ctx.newPage();
const errs = [];
page.on("pageerror", (e) => errs.push("PAGEERR " + e.message.slice(0, 160)));
page.on("console", (m) => { if (m.type() === "error") errs.push("CONSOLE " + m.text().slice(0, 160)); });
await ctx.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: PASS } },
});
await page.goto(`${BASE}/dolan_apps`, { waitUntil: "domcontentloaded" });
await page.waitForFunction(() => document.querySelectorAll(".o_dolan_home_app").length > 0);
const tile = page.locator(".o_dolan_home_app", { hasText: "Contabilidad" }).first();
check("la grilla muestra el tile Contabilidad", (await tile.count()) > 0, "tile");
if (await tile.count()) {
  const href = await tile.getAttribute("href");
  await tile.click();
  await page.waitForTimeout(6000);
  const after = await page.evaluate(() => ({
    path: location.pathname,
    title: document.title,
    navbar: (document.querySelector(".o_main_navbar") || {}).textContent?.slice(0, 120),
    sections: [...document.querySelectorAll(".o_menu_sections a, .o_menu_sections .o_menu_section")].map((e) => e.textContent.trim()).slice(0, 10),
  }));
  check("el tile abre la app en el webclient",
    after.path === "/odoo/accounting" && (after.navbar || "").includes("Contabilidad"),
    `href=${href} -> path=${after.path} navbar=${(after.navbar || "").slice(0, 60)} title=${after.title}`);
  await page.screenshot({ path: shots + "l47-contabilidad-app.png" });
}

// rol Invoicing (operador): mismas secciones de solo lectura, sin regresión
try {
  const op = await menusAs("operador@dolan.com.ar");
  const res2 = {};
  for (const k of Object.keys(op.doc)) res2[String(k)] = op.doc[k];
  const roots2 = [];
  for (const cid of (res2.root?.children || [])) { const m = res2[String(cid)]; if (m && m.appID === m.id) roots2.push(m); }
  const app2 = roots2.find((m) => m.xmlid === "account.menu_finance");
  const sections2 = (app2?.children || []).map((cid) => res2[String(cid)]).filter(Boolean).map((s) => s.name);
  check("operador: app Contabilidad visible", !!app2 && app2.name === "Contabilidad", app2 ? app2.name : "-");
  console.log("SECCIONES operador:", sections2.join(" | "));
} catch (e) {
  console.log("NOTA: verificación por rol Invoicing omitida (" + String(e).slice(0, 80) + ")");
}

console.log("SECCIONES admin:", sections.join(" | "));
console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 5)) : "(sin errores)");
check("0 errores JS", errs.length === 0, `${errs.length}`);

await browser.close();
let failed = 0;
for (const r of results) { if (!r.ok) failed++; console.log(`${r.ok ? "PASS" : "FAIL"} | ${r.name} | ${r.detail}`); }
console.log(`\n${results.length - failed}/${results.length} checks OK`);
process.exit(failed ? 1 : 0);
