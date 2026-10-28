import { chromium } from "playwright";
const b = await chromium.connectOverCDP("http://127.0.0.1:9222");
const pages = b.contexts()[0].pages();
const page = pages.find((p) => p.url().includes("localhost:8070")) || pages[0];
const apps = [
  ["contabilidad", "/odoo/action-305"], ["inventario", "/odoo/action-437"],
  ["compras", "/odoo/action-330"], ["rrhh", "/odoo/action-544"],
  ["flotilla", "/odoo/action-823"], ["mantenimiento", "/odoo/action-848"],
  ["alquileres", "/odoo/action-860"], ["calidad", "/odoo/action-867"],
  ["website", "/odoo/action-website.website_preview?path=/shop"], ["crm", "/odoo/action-510"],
];
for (const [n, u] of apps) {
  await page.goto("http://localhost:8070" + u, { waitUntil: "domcontentloaded", timeout: 40000 }).catch((e) => console.log("NAVFAIL", n, String(e).slice(0, 60)));
  await page.waitForTimeout(5000);
  console.log("NAV", n, (await page.title()).slice(0, 40));
}
b.close();
console.log("NAV_DONE");
