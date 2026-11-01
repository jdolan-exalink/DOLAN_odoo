import { chromium } from "playwright";
// PRD04 · F2-F6 (uncommitted slice): search, role home, density, PWA, notifications
const BASE = process.env.BASE || "http://localhost:8070";
const PASS = process.env.PASS || "admin123";
const LOGIN = process.env.LOGIN || "juan@dolan.com.ar";
const results = [];
const check = (n, ok, d) => { results.push({ n, ok, d }); console.log(`${ok ? "PASS" : "FAIL"} | ${n} | ${d}`); };

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 } });
await ctx.request.post(`${BASE}/web/session/authenticate`, {
  data: { jsonrpc: "2.0", params: { db: "dolan", login: LOGIN, password: PASS } },
});
const page = await ctx.newPage();
const errs = [];
page.on("pageerror", (e) => errs.push(e.message.slice(0, 160)));

// seed data: partner to search + a critical notification for this user
const kw = (model, method, args, kwargs = {}) =>
  ctx.request.post(`${BASE}/web/dataset/call_kw`, {
    data: { jsonrpc: "2.0", params: { model, method, args, kwargs } },
  }).then((r) => r.json()).then((j) => j.result);
const oldOnes = await kw("dolan.notification", "search", [[["name", "=", "QA F6: factura vencida"]]]).catch(() => []);
if (oldOnes && oldOnes.length) { await kw("dolan.notification", "unlink", [oldOnes]).catch(() => null); }
const partners = await kw("res.partner", "search_read", [[]], { fields: ["name"], limit: 1 });
const pname = partners && partners[0] && partners[0].name;
const nCreated = await kw("dolan.notification", "create", [{ name: "QA F6: factura vencida", kind: "critical", body: "Notificacion de prueba" }]);
check("seed: partner encontrado para buscar", !!pname, String(pname));
check("seed: notificacion creada", typeof nCreated === "number" && nCreated > 0, String(nCreated));

await page.goto(`${BASE}/odoo`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".o_dolan_home_grid", { timeout: 45000 });
await page.waitForTimeout(1800);

// ---------- F3: role workspace ----------
const role = await page.$(".o_dolan_home_role .role_chip");
check("F3: rol visible en el home", !!role, role ? (await role.innerText()) : "sin .role_chip");
const kpis = await page.$$(".o_dolan_home_role .o_dolan_kpi");
check("F3: KPIs del rol >= 1", kpis.length >= 1, `${kpis.length} KPIs`);
const quicks = await page.$$(".o_dolan_home_role .o_dolan_quick");
check("F3: acciones rapidas >= 1", quicks.length >= 1, `${quicks.length} bots`);
const gsBtn = await page.$(".o_dolan_home_role .gs_button");
check("F3: boton Buscar en el home", !!gsBtn, !!gsBtn);

// ---------- F6: bell badge ----------
const bell = await page.$(".o_dolan_bell");
check("F6: campana en el systray", !!bell, !!bell);
await page.waitForTimeout(800);
const badge = await page.$(".o_dolan_bell_badge");
check("F6: badge con pendientes", !!badge, badge ? (await badge.innerText()) : "sin badge");

// ---------- F2: global search (g then b) ----------
await page.keyboard.press("g");
await page.keyboard.press("b");
await page.waitForTimeout(500);
const gsOpen = await page.$(".o_dolan_gs input");
check("F2: dialogo de busqueda abre con g b", !!gsOpen, !!gsOpen);
if (gsOpen && pname) {
  await gsOpen.type(pname.slice(0, 12), { delay: 40 });
  await page.waitForTimeout(900);
  const rows = await page.$$(".o_dolan_gs_row");
  check("F2: resultados >= 1 para un partner real", rows.length >= 1, `${rows.length} filas`);
  if (rows.length) {
    await rows[0].click();
    await page.waitForTimeout(1400);
    const form = await page.$(".o_form_view");
    check("F2: Enter/click abre el formulario", !!form, !!form);
  }
  // recents now listed when query empty
  await page.keyboard.press("g");
  await page.keyboard.press("b");
  await page.waitForTimeout(500);
  const rec = await page.$$(".o_dolan_gs_row");
  check("F2: recientes persisten tras abrir", rec.length >= 1, `${rec.length} recientes`);
  await page.keyboard.press("Escape");
  await page.waitForTimeout(400);
  const gone = await page.$(".o_dolan_gs");
  check("F2: Escape cierra", !gone, !!gone);
}

// ---------- F5: PWA ----------
const pwa = await page.evaluate(async () => {
  const mf = await fetch("/dolan_theme/manifest.webmanifest", { credentials: "same-origin" });
  const data = await mf.json();
  const regs = await navigator.serviceWorker.getRegistrations();
  const link = document.querySelector('link[rel="manifest"]');
  return { status: mf.status, display: data.display, start: data.start_url, regs: regs.length, link: !!link };
});
check("F5: manifest 200 + standalone", pwa.status === 200 && pwa.display === "standalone", JSON.stringify(pwa));
check("F5: link manifest en el layout", pwa.link, String(pwa.link));
await page.waitForTimeout(2500);
const regs2 = await page.evaluate(async () => (await navigator.serviceWorker.getRegistrations()).length);
check("F5: service worker registrado", regs2 >= 1, `${regs2} SW`);

// ---------- F4: density toggle ----------
await page.goto(`${BASE}/odoo/contacts?view_type=list`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(2500);
const h1 = await page.evaluate(() => {
  const tr = document.querySelector(".o_list_view .o_list_table tbody tr");
  return tr ? Math.round(tr.getBoundingClientRect().height) : 0;
});
await page.keyboard.press("Control+Alt+d");
await page.waitForTimeout(600);
const dens = await page.evaluate(() => ({
  compact: document.body.classList.contains("o_dolan_compact"),
  ls: localStorage.getItem("dolan_density"),
}));
check("F4: densidad compacta aplica clase + persiste", dens.compact && dens.ls === "compact", JSON.stringify(dens));
const h2 = await page.evaluate(() => {
  const tr = document.querySelector(".o_list_view .o_list_table tbody tr");
  return tr ? Math.round(tr.getBoundingClientRect().height) : 0;
});
check("F4: filas mas bajas en compacta (o sin lista medible)", h1 === 0 || h2 === 0 || h2 <= h1, `h1=${h1} h2=${h2}`);
await page.keyboard.press("Control+Alt+d");
await page.waitForTimeout(300);

// ---------- F6: notification flow ----------
await page.goto(`${BASE}/odoo`, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".o_dolan_bell", { timeout: 45000 });
await page.waitForTimeout(900);
await page.click(".o_dolan_bell");
await page.waitForTimeout(700);
const panel = await page.$(".o_dolan_nc");
const item = await page.$(".o_dolan_nc_item");
check("F6: panel del centro abre con la notificacion", !!panel && !!item, `panel=${!!panel} item=${!!item}`);
if (item) {
  const kind = await (await item.$(".kind")).innerText();
  check("F6: tipo etiquetado con texto (no solo color)", kind.trim().length > 0, kind);
  const readBtn = await item.$('button[aria-label="Marcar como leido"]');
  await readBtn.click();
  await page.waitForTimeout(900);
  const item2 = await page.$(".o_dolan_nc_item");
  check("F6: marcar leido quita la notificacion", !item2, !!item2);
}
const nState = await kw("dolan.notification", "read", [[nCreated]], { fields: ["state"] }).catch(() => null);
const nState2 = nState && nState[0] ? nState[0].state : "?";
check("F6: estado leido persiste en BD", nState2 === "read", nState2);

// ---------- F6 metrics ----------
const metrics = await page.evaluate(() => {
  try { return JSON.parse(localStorage.getItem("dolan_ux_metrics") || "[]").length; } catch { return -1; }
});
check("F6: metricas UX registrando clics", metrics > 0, `${metrics} eventos`);

// ---------- global JS errors ----------
check("0 errores JS en toda la corrida", errs.length === 0, JSON.stringify(errs.slice(0, 3)));

await browser.close();
let failed = 0;
for (const r of results) { if (!r.ok) failed++; }
console.log(`\n${results.length - failed}/${results.length} checks OK`);
process.exit(failed ? 1 : 0);
