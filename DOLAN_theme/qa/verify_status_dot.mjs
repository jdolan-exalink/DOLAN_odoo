import { chromium } from "playwright";

// QA L43: (1) el bundle web.assets_web NO debe contener el fallback de error CSS
//         (libsass revienta con min(70vh, 560px) -> "Incompatible units: 'px' and 'vh'")
//         (2) el status dot del chat DOLAN AI debe reflejar estados reales:
//             ok = conectado, err = sin conexión, pending = estado no disponible.
const BASE = process.env.BASE || "http://localhost:8070";
const DB = process.env.DB || "dolan";
const LOGIN = process.env.LOGIN || "juan@dolan.com.ar";
const PASS = process.env.PASS || "admin123";

const results = [];
const check = (name, ok, detail) => { results.push({ name, ok, detail }); };

// ---------- 1. bundle CSS sin error ----------
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 860 } });
const req = ctx.request;
await req.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: DB, login: LOGIN, password: PASS } },
});
const html = await (await req.get(`${BASE}/odoo`)).text();
const cssHref = (html.match(/href="([^"]*web\.assets_web\.min\.css[^"]*)"/) || [])[1];
if (!cssHref) {
  check("bundle: link web.assets_web.min.css presente", false, "no se encontró el link en /odoo");
} else {
  const css = await (await req.get(`${BASE}${cssHref}`)).text();
  const hasErr = css.includes("CSS error message") || css.includes("A css error occurred");
  check("bundle: sin fallback de error CSS", !hasErr,
    hasErr ? `el bundle trae el banner de error CSS (${cssHref})` : `compila limpio (${cssHref}, ${css.length} b)`);
}

// ---------- 2. estados del status dot ----------
async function dotState(statusResult, label, shot) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 860 } });
  const page = await context.newPage();
  const errs = [];
  page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 140)); });
  await context.request.post(`${BASE}/web/session/authenticate`, {
    data: { jsonrpc: "2.0", params: { db: DB, login: LOGIN, password: PASS } },
  });
  if (statusResult !== undefined) {
    await page.route("**/dolan_ai/status", (r) => r.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ jsonrpc: "2.0", id: null, result: statusResult }),
    }));
  }
  await page.goto(`${BASE}/odoo`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".o_dolan_ai_btn", { timeout: 30000 });
  await page.click(".o_dolan_ai_btn");
  await page.waitForSelector(".o_dolan_ai_win", { timeout: 15000 });
  await page.waitForTimeout(2000); // deja terminar checkStatus()
  const info = await page.evaluate(() => {
    const dot = document.querySelector(".o_dolan_ai_status_dot");
    if (!dot) return { present: false };
    const cs = getComputedStyle(dot);
    const r = dot.getBoundingClientRect();
    return {
      present: true, cls: dot.className, title: dot.title,
      w: Math.round(r.width), h: Math.round(r.height), bg: cs.backgroundColor,
      visible: !!(r.width && r.height),
    };
  });
  await page.screenshot({ path: new URL(`./shots/${shot}`, import.meta.url).pathname });
  check(`dot ${label}`, true, JSON.stringify(info) + (errs.length ? ` | console: ${JSON.stringify(errs.slice(0, 3))}` : ""));
  await context.close();
  return info;
}

const admin = await dotState(undefined, "admin (status real)", "l43-dot-admin.png");
check("dot: presente y visible 8x8", admin.present && admin.visible && admin.w === 8 && admin.h === 8,
  `rect ${admin.w}x${admin.h}`);
check("dot: admin conectado -> clase ok", (admin.cls || "").includes(" ok") || (admin.cls || "").endsWith("ok"),
  `cls="${admin.cls}" title="${admin.title}"`);
check("dot: título informa Conectado", /conectado/i.test(admin.title || ""), `title="${admin.title}"`);

const noAuth = await dotState({ error: "no_autorizado" }, "status no autorizado", "l43-dot-noauth.png");
check("dot: status no disponible -> gris pending (no rojo)",
  (noAuth.cls || "").includes("pending") && /no disponible/i.test(noAuth.title || ""),
  `cls="${noAuth.cls}" title="${noAuth.title}" bg=${noAuth.bg}`);

const down = await dotState({ connected: false, device_pending: false }, "sin conexión", "l43-dot-offline.png");
check("dot: connected=false -> rojo err", (down.cls || "").includes("err"),
  `cls="${down.cls}" title="${down.title}" bg=${down.bg}`);

await browser.close();

let failed = 0;
for (const r of results) {
  if (!r.ok) failed++;
  console.log(`${r.ok ? "PASS" : "FAIL"} | ${r.name} | ${r.detail}`);
}
console.log(`\n${results.length - failed}/${results.length} checks OK`);
process.exit(failed ? 1 : 0);
