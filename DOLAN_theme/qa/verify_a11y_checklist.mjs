import { chromium } from "playwright";
// PRD04 · F1 — checklist WCAG 2.1 AA sobre componentes propios (light + dark)
const BASE = process.env.BASE || "http://localhost:8070";
const PASS = process.env.PASS || "admin123";
const results = [];
const check = (n, ok, d) => results.push({ n, ok, d });

const browser = await chromium.launch();

async function audit(theme) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 } });
  await ctx.addInitScript((t) => { try { localStorage.setItem("dolan_theme_mode", t); } catch (e) {} }, theme);
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 120)));
  await ctx.request.post(`${BASE}/web/session/authenticate`, {
    data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: PASS } },
  });
  await page.goto(`${BASE}/odoo`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".o_dolan_home_grid", { timeout: 45000 });
  await page.waitForTimeout(1200);

  const grid = await page.evaluate(() => {
    const lum = (c) => {
      const [r, g, b] = c.match(/\d+(\.\d+)?/g).slice(0, 3).map(Number).map((v) => {
        v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const ratio = (fg, bg) => { const a = lum(fg), b = lum(bg); const hi = Math.max(a, b), lo = Math.min(a, b); return (hi + 0.05) / (lo + 0.05); };
    const bgOf = (el) => { let n = el; while (n) { const c = getComputedStyle(n).backgroundColor; if (c && !/rgba\(0, 0, 0, 0\)|transparent/.test(c)) return c; n = n.parentElement; } return "rgb(255,255,255)"; };
    const out = { theme: document.documentElement.dataset.dolanTheme || "light" };
    const name = document.querySelector(".o_dolan_home_grid .name");
    if (name) out.gridName = { c: getComputedStyle(name).color, bg: bgOf(name), r: Math.round(ratio(getComputedStyle(name).color, bgOf(name)) * 100) / 100, fs: getComputedStyle(name).fontSize };
    const brand = document.querySelector(".o_menu_brand, .o_main_navbar .o_main_navbar_brand, .o_main_navbar a, .o_main_navbar .dropdown-toggle");
    if (brand) out.nav = { c: getComputedStyle(brand).color, bg: bgOf(brand), r: Math.round(ratio(getComputedStyle(brand).color, bgOf(brand)) * 100) / 100 };
    // accesibilidad: nombres accesibles en navbar + grilla
    const named = (e) => (e.textContent || "").trim() || e.getAttribute("aria-label") || e.getAttribute("title") ||
      !!e.querySelector('[aria-label], [title], img[alt]:not([alt=""])');
    const noName = [...document.querySelectorAll(".o_main_navbar button, .o_main_navbar a, .o_dolan_home_grid a")]
      .filter((e) => !named(e)).length;
    out.controlsWithoutName = noName;
    // estados sin depender del color: los tags de estado llevan texto
    const tags = [...document.querySelectorAll(".dolan_tag, .o_dolan_badge, .badge")];
    out.tagsWithoutText = tags.filter((t) => !(t.textContent || "").trim()).length;
    out.tagsTotal = tags.length;
    // focus visible: regla en nuestras hojas
    let focusRules = 0;
    for (const sheet of document.styleSheets) {
      try { for (const r of sheet.cssRules) if (String(r.selectorText || "").includes("focus-visible")) focusRules++; } catch (e) {}
    }
    out.focusVisibleRules = focusRules;
    return out;
  });
  await ctx.close();
  return { grid, errs };
}

const light = await audit("light");
const dark = await audit("dark");

check(`[light] contraste del nombre de app >= 4.5 (AA)`, light.grid.gridName && light.grid.gridName.r >= 4.5, JSON.stringify(light.grid.gridName));
check(`[light] contraste del navbar >= 4.5 (AA)`, light.grid.nav && light.grid.nav.r >= 4.5, JSON.stringify(light.grid.nav));
check(`[dark] contraste del nombre de app >= 4.5 (AA)`, dark.grid.gridName && dark.grid.gridName.r >= 4.5, JSON.stringify(dark.grid.gridName));
check(`[dark] contraste del navbar >= 4.5 (AA)`, dark.grid.nav && dark.grid.nav.r >= 4.5, JSON.stringify(dark.grid.nav));
check(`controles sin nombre accesible = 0`, light.grid.controlsWithoutName === 0 && dark.grid.controlsWithoutName === 0,
  `light=${light.grid.controlsWithoutName} dark=${dark.grid.controlsWithoutName}`);
check(`badges/estados con texto (no sólo color)`, light.grid.tagsWithoutText === 0 && dark.grid.tagsWithoutText === 0,
  `light ${light.grid.tagsWithoutText}/${light.grid.tagsTotal} dark ${dark.grid.tagsWithoutText}/${dark.grid.tagsTotal}`);
check(`reglas :focus-visible presentes en nuestros assets`, (light.grid.focusVisibleRules + dark.grid.focusVisibleRules) > 0,
  `${light.grid.focusVisibleRules + dark.grid.focusVisibleRules} reglas`);
check(`0 errores JS en ambas auditorías`, light.errs.length === 0 && dark.errs.length === 0,
  JSON.stringify([...light.errs, ...dark.errs].slice(0, 3)));

await browser.close();
let failed = 0;
for (const r of results) { if (!r.ok) failed++; console.log(`${r.ok ? "PASS" : "FAIL"} | ${r.n} | ${r.d}`); }
console.log(`\n${results.length - failed}/${results.length} checks OK`);
process.exit(failed ? 1 : 0);
