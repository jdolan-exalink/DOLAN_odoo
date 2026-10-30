import { chromium } from "playwright";

// QA L48 (S8/P2 · C9): tarjeta "Cheques de terceros" en el tablero de dolan_dash.
const BASE = process.env.BASE || "http://localhost:8070";
const PASS = process.env.PASS || "admin123";
const shots = new URL("./shots/", import.meta.url).pathname;
const results = [];
const check = (name, ok, detail) => results.push({ name, ok, detail });

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 } });
const page = await ctx.newPage();
const errs = [];
page.on("pageerror", (e) => errs.push("PAGEERR " + e.message.slice(0, 200)));
page.on("console", (m) => { if (m.type() === "error") errs.push("CONSOLE " + m.text().slice(0, 200)); });
await ctx.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: PASS } },
});

await page.goto(`${BASE}/odoo/action-817`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".dolan_kpis", { timeout: 45000 });
await page.waitForTimeout(2500);

const cards = await page.evaluate(() =>
  [...document.querySelectorAll(".dolan_card")].map((c) => ({
    label: c.querySelector(".dolan_icon")?.textContent?.trim(),
    value: c.querySelector(".dolan_value")?.textContent?.trim(),
    hint: c.querySelector(".dolan_hint")?.textContent?.trim(),
  })));
check("tarjetas del tablero (>=9)", cards.length >= 9, cards.map((c) => c.label).join(" | "));
const cheq = cards.find((c) => /^Cheques/.test(c.label || ""));
check("tarjeta 'Cheques de terceros' presente", !!cheq, cheq ? JSON.stringify(cheq) : "no está");
check("hint de cheques con monto y propios", !!cheq && /propios/.test(cheq.hint || ""), cheq ? cheq.hint : "-");

// click en la tarjeta -> serie + detalle activo
if (cheq) {
  await page.locator(".dolan_card", { hasText: "Cheques" }).first().click();
  await page.waitForTimeout(2500);
  const sec = await page.evaluate(() => ({
    title: document.querySelector(".dolan_section_title")?.textContent?.trim(),
    bars: document.querySelectorAll(".dolan_bar").length,
    active: [...document.querySelectorAll(".dolan_block_active")].map((b) =>
      b.querySelector(".dolan_detail_title")?.textContent?.trim()),
    rows: document.querySelectorAll(".dolan_table").length,
  }));
  check("serie 'Cheques (cantidad, 6 meses)' con barras", /Cheques/.test(sec.title || "") && sec.bars === 6,
    JSON.stringify({ title: sec.title, bars: sec.bars }));
  check("bloque 'Últimos cheques' activo", (sec.active || []).some((t) => /cheques/i.test(t || "")),
    JSON.stringify(sec.active));
  await page.screenshot({ path: shots + "l48-tablero-cheques.png" });
}

console.log("TARJETAS:", JSON.stringify(cards));
console.log("CONSOLE:", errs.length ? JSON.stringify([...new Set(errs)].slice(0, 5)) : "(sin errores)");
check("0 errores JS (plantilla Owl)", errs.length === 0, `${errs.length}`);

await browser.close();
let failed = 0;
for (const r of results) { if (!r.ok) failed++; console.log(`${r.ok ? "PASS" : "FAIL"} | ${r.name} | ${r.detail}`); }
console.log(`\n${results.length - failed}/${results.length} checks OK`);
process.exit(failed ? 1 : 0);
