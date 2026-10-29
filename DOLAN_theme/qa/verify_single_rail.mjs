import { chromium } from "playwright";

// QA L44: una sola sidebar. Las páginas standalone /dolan_* NO deben traer la rail
// embebida (DOLAN_ai/embed_rail.js); deben tener un link "Volver" y el contenido
// sin desplazar. La rail del webclient (DOLAN_theme) se conserva y se verifica.
const BASE = process.env.BASE || "http://localhost:8070";
const shots = new URL("./shots/", import.meta.url).pathname;
const PAGES = [
  "/dolan_apps", "/dolan_ai", "/dolan_alquileres", "/dolan_codigo_barras",
  "/dolan_contabilidad", "/dolan_flotilla", "/dolan_mantenimiento", "/dolan_suscripciones",
];
const results = [];
const check = (name, ok, detail) => results.push({ name, ok, detail });

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 } });
const page = await ctx.newPage();
const errs = [];
page.on("pageerror", (e) => errs.push("PAGEERR " + e.message.slice(0, 140)));
page.on("console", (m) => { if (m.type() === "error") errs.push("CONSOLE " + m.text().slice(0, 140)); });
await ctx.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: process.env.PASS || "admin123" } },
});

for (const path of PAGES) {
  const resp = await page.goto(`${BASE}${path}`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2500);
  const info = await page.evaluate(() => {
    const back = [...document.querySelectorAll("a")].find((a) => /volver/i.test(a.textContent || ""));
    return {
      rails: document.querySelectorAll(".o_dolan_rail").length,
      bodyPadLeft: getComputedStyle(document.body).paddingLeft,
      backHref: back ? back.getAttribute("href") : null,
      backText: back ? back.textContent.trim().slice(0, 30) : null,
      overflowX: document.documentElement.scrollWidth > window.innerWidth,
    };
  });
  const label = `página ${path}`;
  check(`${label}: HTTP 200`, resp.status() === 200, `status=${resp.status()}`);
  check(`${label}: sin rail embebida`, info.rails === 0, `rails=${info.rails}`);
  check(`${label}: contenido sin desplazar (padding-left != 240px)`, info.bodyPadLeft !== "240px", `padding-left=${info.bodyPadLeft}`);
  check(`${label}: link "Volver" a /odoo`, info.backHref === "/odoo", `href=${info.backHref} text="${info.backText}"`);
  check(`${label}: sin scroll horizontal`, !info.overflowX, "ok");
}

// home grid: conserva grilla + toggle de tema (sin rail)
await page.goto(`${BASE}/dolan_apps`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(2500);
const grid = await page.evaluate(() => ({
  apps: document.querySelectorAll(".o_dolan_home_app").length,
  toggle: !!document.querySelector("#theme-toggle"),
  icon: document.querySelector(".icon_wrap img") ? Math.round(document.querySelector(".icon_wrap img").getBoundingClientRect().width) : 0,
}));
check("home grid: 38 apps + toggle + iconos 70px", grid.apps === 38 && grid.toggle && grid.icon === 70, JSON.stringify(grid));
await page.click("#theme-toggle");
await page.waitForTimeout(600);
const dark = await page.evaluate(() => ({
  attr: document.documentElement.dataset.dolanTheme,
  bg: getComputedStyle(document.body).backgroundColor,
}));
check("home grid: modo oscuro sigue funcionando", dark.attr === "dark" && dark.bg === "rgb(26, 26, 46)", JSON.stringify(dark));
await page.screenshot({ path: shots + "l44-single-rail-home-dark.png" });

// rail del webclient: se conserva intacta
await page.goto(`${BASE}/odoo/action-817`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(5000);
const wc = await page.evaluate(() => {
  const rail = document.querySelector(".o_dolan_rail");
  const am = document.querySelector(".o_action_manager");
  return {
    rails: document.querySelectorAll(".o_dolan_rail").length,
    toggle: !!document.querySelector(".o_dolan_rail_toggle"),
    items: document.querySelectorAll(".o_dolan_rail_item").length,
    railW: rail ? Math.round(rail.getBoundingClientRect().width) : null,
    amMargin: am ? getComputedStyle(am).marginLeft : null,
  };
});
check("webclient: rail propia intacta (toggle + 38 apps + offset)",
  wc.rails === 1 && wc.toggle && wc.items === 38 && wc.railW === 240 && wc.amMargin === "240px", JSON.stringify(wc));

await browser.close();
const seen = [...new Set(errs)];
check("sin errores JS en todo el barrido", seen.length === 0, JSON.stringify(seen.slice(0, 5)));

let failed = 0;
for (const r of results) { if (!r.ok) failed++; console.log(`${r.ok ? "PASS" : "FAIL"} | ${r.name} | ${r.detail}`); }
console.log(`\n${results.length - failed}/${results.length} checks OK`);
process.exit(failed ? 1 : 0);
