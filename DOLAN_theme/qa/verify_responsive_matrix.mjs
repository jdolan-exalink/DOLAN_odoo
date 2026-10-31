import { chromium } from "playwright";
// PRD04 · F1: matriz minima de pruebas — grilla Inicio dentro del webclient
const BASE = process.env.BASE || "http://localhost:8070";
const PASS = process.env.PASS || "admin123";
const VIEWPORTS = [
  [1920, 1080], [2560, 1440], [1366, 768], [1024, 768],
  [820, 1180], [768, 1024], [414, 896], [360, 740],
];
const results = [];
const check = (n, ok, d) => results.push({ n, ok, d });
const browser = await chromium.launch();
for (const [w, h] of VIEWPORTS) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, hasTouch: w < 1200 });
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 120)));
  await ctx.request.post(`${BASE}/web/session/authenticate`, {
    data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: PASS } },
  });
  await page.goto(`${BASE}/odoo`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".o_dolan_home_grid", { timeout: 45000 });
  await page.waitForTimeout(1500);
  const s = await page.evaluate(() => {
    const de = document.documentElement;
    const apps = [...document.querySelectorAll(".o_dolan_home_grid .o_dolan_home_app")];
    const icon = document.querySelector(".o_dolan_home_grid .icon_wrap img");
    const tap = apps[0] ? Math.round(apps[0].getBoundingClientRect().height) : 0;
    return {
      overflow: de.scrollWidth > window.innerWidth + 1,
      apps: apps.length,
      icon: icon ? Math.round(icon.getBoundingClientRect().width) : 0,
      tap, navbar: !!document.querySelector(".o_main_navbar"),
      rail: document.querySelectorAll(".o_dolan_rail").length,
    };
  });
  const tag = `${w}x${h}`;
  check(`${tag}: sin overflow horizontal`, !s.overflow, JSON.stringify(s));
  check(`${tag}: grilla con apps`, s.apps >= 10, `${s.apps} apps`);
  check(`${tag}: navbar sin rail`, s.navbar && s.rail === 0, `navbar=${s.navbar} rail=${s.rail}`);
  if (w >= 1200) check(`${tag}: iconos 70px`, s.icon === 70, `${s.icon}px`);
  if (w < 768) check(`${tag}: target tactil >=44px`, s.tap >= 44, `${s.tap}px`);
  check(`${tag}: 0 errores JS`, errs.length === 0, JSON.stringify(errs.slice(0, 2)));
  await ctx.close();
}
await browser.close();
let failed = 0;
for (const r of results) { if (!r.ok) failed++; console.log(`${r.ok ? "PASS" : "FAIL"} | ${r.n} | ${r.d}`); }
console.log(`\n${results.length - failed}/${results.length} checks OK`);
process.exit(failed ? 1 : 0);
