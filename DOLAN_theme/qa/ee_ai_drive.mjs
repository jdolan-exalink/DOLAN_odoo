import { chromium } from "playwright";
const USER = process.env.EE_USER, PASS = process.env.EE_PASS;
const b = await chromium.connectOverCDP("http://127.0.0.1:9223");
const ctx = b.contexts()[0];
let page = ctx.pages().find(p => p.url().includes("exalink"));
if (!page) page = await ctx.newPage();
if (page.url().includes("login")) {
  await page.fill('#login, input[name="login"]', USER);
  await page.fill('#password, input[name="password"]', PASS);
  await Promise.all([page.waitForNavigation({ timeout: 60000 }).catch(() => {}), page.click('button[type="submit"], .oe_login_button')]);
  await page.waitForTimeout(7000);
}
console.log("URL:", page.url().slice(0, 60));
// buscar el botón IA en la topbar (odoo.com usa un botón flotante/topbar)
const probe = await page.evaluate(() => {
  const cands = [...document.querySelectorAll("button, a, [role=button]")].filter(e => {
    const t = (e.getAttribute("title") || e.getAttribute("aria-label") || e.textContent || "").toLowerCase();
    return t.includes("ia") || t.includes("ai ") || t.includes("odoo ai") || t.includes("asistente");
  }).map(e => ({ cls: e.className.toString().slice(0, 70), title: e.getAttribute("title") || e.getAttribute("aria-label"), txt: e.textContent.trim().slice(0, 30) }));
  return cands.slice(0, 10);
});
console.log("CANDIDATOS IA:", JSON.stringify(probe));
// screenshot de la topbar completa para ubicar el botón
await page.screenshot({ path: "/root/DOLAN_odoo20/DOLAN_theme/qa/shots/l34-ee-topbar.png" });
// buscar íconos del topbar derecho
const topbar = await page.evaluate(() => {
  const bar = document.querySelector(".o_main_navbar, header");
  if (!bar) return null;
  return [...bar.querySelectorAll("button, a")].map(e => ({
    cls: e.className.toString().slice(0, 60),
    title: e.getAttribute("title") || e.getAttribute("aria-label") || "",
    txt: e.textContent.trim().slice(0, 20),
  })).slice(0, 20);
});
console.log("TOPBAR:", JSON.stringify(topbar));
await b.close();
