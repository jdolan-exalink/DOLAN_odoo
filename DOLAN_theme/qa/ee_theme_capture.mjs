import { chromium } from "playwright";
const USER = process.env.EE_USER, PASS = process.env.EE_PASS;
const OUT = "/root/DOLAN_odoo20/DOLAN_theme/docs/evidence/ee-theme-v2";
const fs = await import("node:fs");
fs.mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
await page.goto("https://exalink.odoo.com/web/login", { waitUntil: "domcontentloaded", timeout: 60000 });
await page.fill('#login, input[name="login"]', USER);
await page.fill('#password, input[name="password"]', PASS);
await Promise.all([page.waitForNavigation({ timeout: 60000 }).catch(() => {}), page.click('button[type="submit"], .oe_login_button')]);
await page.waitForTimeout(7000);
// 1) HOME GRID (claro)
await page.goto("https://exalink.odoo.com/odoo", { waitUntil: "domcontentloaded" }).catch(() => {});
await page.waitForTimeout(7000);
await page.screenshot({ path: `${OUT}/01-home-grid-claro.png` });
// analizar estructura del grid
const grid = await page.evaluate(() => {
  const apps = [...document.querySelectorAll(".o_app")].slice(0, 5).map(e => ({
    cls: e.className.toString().slice(0, 100),
    icon: e.querySelector("img") ? { src: e.querySelector("img").src.slice(0, 40), w: e.querySelector("img").getBoundingClientRect().width, h: e.querySelector("img").getBoundingClientRect().height } : null,
    label: e.querySelector("[class*=name]")?.textContent?.trim()?.slice(0, 20),
  }));
  const container = document.querySelector(".o_apps, .o_home_menu, [class*=apps_menu]");
  const gridStyle = container ? {
    display: getComputedStyle(container).display,
    gridTemplateColumns: getComputedStyle(container).gridTemplateColumns,
    gap: getComputedStyle(container).gap,
  } : null;
  return { apps, gridStyle };
});
console.log("GRID:", JSON.stringify(grid, null, 1).slice(0, 800));
// 2) HOME GRID (oscuro) — buscar toggle
const themeToggle = await page.evaluate(() => {
  const btns = [...document.querySelectorAll("button, a, [role=button]")].filter(b => {
    const t = (b.getAttribute("title") || b.getAttribute("aria-label") || "").toLowerCase();
    return t.includes("dark") || t.includes("theme") || t.includes("oscuro") || t.includes("tema");
  }).map(b => ({ cls: b.className.toString().slice(0, 60), title: b.getAttribute("title") }));
  return btns;
});
console.log("TOGGLE:", JSON.stringify(themeToggle));
// toggle dark via settings si hay botón
const tog = page.locator('[title*="dark"], [title*="theme"], [title*="oscuro"]').first();
if (await tog.count().catch(() => 0)) { await tog.click(); await page.waitForTimeout(4000); }
else {
  // via settings dropdown
  await page.locator('[title="Ajustes"], [title="Settings"], .o_user_menu').first().click();
  await page.waitForTimeout(2000);
  const darkOpt = page.locator("text=dark mode, text=modo oscuro, text=Dark Mode").first();
  if (await darkOpt.count().catch(() => 0)) { await darkOpt.click(); await page.waitForTimeout(4000); }
  else { await page.keyboard.press("Escape"); await page.waitForTimeout(1000); }
}
await page.goto("https://exalink.odoo.com/odoo", { waitUntil: "domcontentloaded" }).catch(() => {});
await page.waitForTimeout(7000);
await page.screenshot({ path: `${OUT}/02-home-grid-oscuro.png` });
const darkInfo = await page.evaluate(() => {
  const html = document.documentElement;
  const body = document.body;
  return { htmlCls: html.className.slice(0, 80), bodyBg: getComputedStyle(body).backgroundColor, htmlDataTheme: html.getAttribute("data-theme") || html.getAttribute("data-color-scheme") || "sin attr" };
});
console.log("DARK:", JSON.stringify(darkInfo));
// 3) Volver a claro y capturar vistas clave
await page.evaluate(() => { document.documentElement.classList.remove("o_dark"); });
await page.goto("https://exalink.odoo.com/odoo", { waitUntil: "domcontentloaded" }).catch(() => {});
await page.waitForTimeout(5000);
const apps = await page.evaluate(() => [...document.querySelectorAll(".o_app")].map(e => (e.querySelector("[class*=name]")?.textContent || "").trim().slice(0, 25)));
console.log("APPS DISPONIBLES:", JSON.stringify(apps));
// capturar 4 vistas clave (Facturación, Inventario, Contactos, Ajustes)
for (const k of ["Contabilidad", "Inventario", "Contactos", "Ajustes"]) {
  const t = page.locator(".o_app", { hasText: new RegExp(`^${k}`, "i") }).first();
  if (!(await t.count().catch(() => 0))) { console.log("SIN", k); continue; }
  await t.click({ timeout: 8000 });
  await page.waitForTimeout(6000);
  await page.screenshot({ path: `${OUT}/03-${k.toLowerCase()}.png` });
  const struct = await p.evaluate(() => {
    const nav = document.querySelector(".o_main_navbar");
    const rail = document.querySelector(".o_app_menu_sidebar, .o_burger_menu_content");
    return { navCls: nav?.className?.slice(0, 80), rail: rail?.className?.slice(0, 80) || "sin rail", breadcrumb: document.querySelector(".o_menu_brand")?.textContent?.slice(0, 30) };
  });
  console.log(k.toUpperCase(), JSON.stringify(struct));
  await page.goto("https://exalink.odoo.com/odoo", { waitUntil: "domcontentloaded" }).catch(() => {});
  await page.waitForTimeout(5000);
}
await browser.close();
