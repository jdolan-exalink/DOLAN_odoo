import { chromium } from "playwright";
const USER = process.env.EE_USER, PASS = process.env.EE_PASS;
const OUT = "/root/DOLAN_odoo20/DOLAN_theme/docs/evidence/ee-theme-v2";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
await page.goto("https://exalink.odoo.com/web/login", { waitUntil: "domcontentloaded", timeout: 60000 });
await page.fill('#login, input[name="login"]', USER);
await page.fill('#password, input[name="password"]', PASS);
await Promise.all([page.waitForNavigation({ timeout: 60000 }).catch(() => {}), page.click('button[type="submit"], .oe_login_button')]);
await page.waitForTimeout(7000);
await page.goto("https://exalink.odoo.com/odoo", { waitUntil: "domcontentloaded" }).catch(() => {});
await page.waitForTimeout(7000);
// estructura CSS del grid
const analysis = await page.evaluate(() => {
  const apps = [...document.querySelectorAll(".o_app")].slice(0, 3).map(e => {
    const cs = getComputedStyle(e);
    return {
      cls: e.className.toString().slice(0, 120),
      display: cs.display, flexDirection: cs.flexDirection,
      alignItems: cs.alignItems, justifyContent: cs.justifyContent,
      width: e.getBoundingClientRect().width, height: e.getBoundingClientRect().height,
      borderRadius: cs.borderRadius, padding: cs.padding,
      iconSize: e.querySelector("img") ? e.querySelector("img").getBoundingClientRect().width : 0,
      labelSize: e.querySelector("[class*=name]") ? getComputedStyle(e.querySelector("[class*=name]")).fontSize : "?",
      labelWeight: e.querySelector("[class*=name]") ? getComputedStyle(e.querySelector("[class*=name]")).fontWeight : "?",
      labelColor: e.querySelector("[class*=name]") ? getComputedStyle(e.querySelector("[class*=name]")).color : "?",
    };
  });
  const parent = apps[0] ? document.querySelector(".o_app").parentElement : null;
  const parentStyle = parent ? {
    cls: parent.className.slice(0, 80), display: getComputedStyle(parent).display,
    gridCols: getComputedStyle(parent).gridTemplateColumns, gap: getComputedStyle(parent).gap,
    maxWidth: getComputedStyle(parent).maxWidth, padding: getComputedStyle(parent).padding,
  } : null;
  // clases del body/html para dark mode
  const body = document.body, html = document.documentElement;
  const bodyStyles = { bg: getComputedStyle(body).backgroundColor, color: getComputedStyle(body).color };
  // navbar
  const nav = document.querySelector(".o_main_navbar");
  const navStyle = nav ? { bg: getComputedStyle(nav).backgroundColor, h: nav.getBoundingClientRect().height, cls: nav.className.slice(0, 80) } : null;
  // clases dark
  const darkClasses = [...html.classList, ...body.classList].filter(c => /dark|theme|scheme/i.test(c));
  return { apps, parentStyle, bodyStyles, navStyle, darkClasses, htmlData: html.getAttribute("data-color-scheme"), bodyData: body.getAttribute("data-color-scheme") };
});
console.log("ANALYSIS:", JSON.stringify(analysis, null, 1).slice(0, 2500));
// captura home claro
await page.screenshot({ path: `${OUT}/01-home-grid-claro.png` });
// activar dark vía Ajustes > usuario
await page.locator(".o_user_menu").first().click();
await page.waitForTimeout(3000);
// buscar la opción de theme/dark en el dropdown
const dropdown = await page.evaluate(() => {
  const items = [...document.querySelectorAll(".o_dropdown_menu a, .o_dropdown_menu [role=menuitem], .dropdown-menu a")].map(a => ({ txt: a.textContent.trim().slice(0, 40), cls: a.className.slice(0, 50) }));
  return items;
});
console.log("DROPDOWN:", JSON.stringify(dropdown).slice(0, 500));
// probar toggling dark via URL param o localStorage
await page.evaluate(() => { localStorage.setItem("colorScheme", "dark"); });
await page.reload({ waitUntil: "domcontentloaded" });
await page.waitForTimeout(7000);
const darkState = await page.evaluate(() => {
  const html = document.documentElement;
  const body = document.body;
  return { htmlCls: html.className.slice(0, 100), bodyBg: getComputedStyle(body).backgroundColor, dataColorScheme: html.getAttribute("data-color-scheme"), bodyDataScheme: body.getAttribute("data-color-scheme") };
});
console.log("DARK STATE:", JSON.stringify(darkState));
await page.screenshot({ path: `${OUT}/02-home-grid-oscuro.png` });
// vista de Facturación (para comparar estructura interna)
const cont = page.locator(".o_app", { hasText: /Contabilidad/i }).first();
if (await cont.count().catch(() => 0)) {
  await cont.click(); await page.waitForTimeout(6000);
  await page.screenshot({ path: `${OUT}/03-contabilidad.png` });
  const inner = await page.evaluate(() => {
    const nav = document.querySelector(".o_main_navbar");
    return { navbarH: nav?.getBoundingClientRect()?.height, navbarBg: nav ? getComputedStyle(nav).backgroundColor : null };
  });
  console.log("CONTABILIDAD:", JSON.stringify(inner));
}
await browser.close();
