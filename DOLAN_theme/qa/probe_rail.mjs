import { chromium } from "playwright";

// QA L44: comportamiento del rail lateral de apps (DOLAN_theme.NavBar.Rail)
const BASE = process.env.BASE || "http://localhost:8070";
const shots = new URL("./shots/", import.meta.url).pathname;
const results = [];
const check = (name, ok, detail) => { results.push({ name, ok, detail }); };

const browser = await chromium.launch();

async function newPage(width = 1440, height = 950) {
  const ctx = await browser.newContext({ viewport: { width, height } });
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push("PAGEERR " + e.message.slice(0, 160)));
  page.on("console", (m) => { if (m.type() === "error") errs.push("CONSOLE " + m.text().slice(0, 160)); });
  await ctx.request.post(`${BASE}/web/session/authenticate`, {
    data: { jsonrpc: "2.0", params: { db: "dolan", login: "juan@dolan.com.ar", password: process.env.PASS || "admin123" } },
  });
  return { page, errs, ctx };
}

// ---------- desktop (webclient) ----------
{
  const { page, errs, ctx } = await newPage();
  await page.goto(`${BASE}/odoo/action-817`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);

  const before = await page.evaluate(() => {
    const rail = document.querySelector(".o_dolan_rail");
    const am = document.querySelector(".o_action_manager");
    const items = [...document.querySelectorAll(".o_dolan_rail_item")];
    const r = rail ? rail.getBoundingClientRect() : null;
    const cs = rail ? getComputedStyle(rail) : null;
    return {
      url: location.pathname,
      rail: !!rail,
      rect: r ? { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } : null,
      display: cs ? cs.display : null,
      zIndex: cs ? cs.zIndex : null,
      items: items.length,
      firstLabels: items.slice(0, 5).map((i) => i.querySelector(".o_dolan_rail_label")?.textContent),
      brokenImgs: items.filter((i) => { const im = i.querySelector("img"); return im && !im.complete; }).length,
      active: items.filter((i) => i.classList.contains("o_dolan_rail_active")).map((i) => i.textContent.trim().slice(0, 20)),
      actionManagerMarginLeft: am ? getComputedStyle(am).marginLeft : null,
      // ¿hay solape? (el elemento más a la izquierda del contenido)
      contentLeft: am ? Math.round(am.getBoundingClientRect().x) : null,
      railRight: r ? Math.round(r.right) : null,
      compact: document.body.classList.contains("dolan-compact"),
      html: rail ? rail.outerHTML.slice(0, 300) : null,
    };
  });
  console.log("DESKTOP BEFORE:", JSON.stringify(before, null, 1));
  await page.screenshot({ path: shots + "l44-rail-desktop.png" });

  // click en un item de la rail (Compras)
  const target = page.locator('.o_dolan_rail_item[data-menu-xmlid="purchase.menu_purchase_root"]');
  if (await target.count()) {
    const urlBefore = page.url();
    await target.click();
    await page.waitForTimeout(3000);
    const after = await page.evaluate(() => ({
      url: location.pathname,
      active: [...document.querySelectorAll(".o_dolan_rail_item.o_dolan_rail_active")]
        .map((i) => i.getAttribute("data-menu-xmlid")),
      railStill: !!document.querySelector(".o_dolan_rail"),
      railCount: document.querySelectorAll(".o_dolan_rail").length,
      crumbs: document.querySelector(".o_control_panel")?.textContent?.slice(0, 80),
    }));
    console.log("CLICK COMPRAS:", JSON.stringify({ urlBefore, ...after }));
    check("rail: click navega a la app", after.url !== before.url, `${before.url} -> ${after.url}`);
    check("rail: app activa resaltada", after.active.length === 1, JSON.stringify(after.active));
    check("rail: un solo rail tras navegar", after.railCount === 1, `count=${after.railCount}`);
    await page.screenshot({ path: shots + "l44-rail-tras-click.png" });
  } else {
    check("rail: item Compras presente", false, "no se encontró purchase.menu_purchase_root");
  }

  // compactar / expandir
  await page.locator(".o_dolan_rail_toggle").click();
  await page.waitForTimeout(800);
  const compact = await page.evaluate(() => {
    const rail = document.querySelector(".o_dolan_rail");
    const am = document.querySelector(".o_action_manager");
    return {
      body: document.body.classList.contains("dolan-compact"),
      railW: rail ? Math.round(rail.getBoundingClientRect().width) : null,
      amMargin: am ? getComputedStyle(am).marginLeft : null,
      ls: localStorage.getItem("dolan_rail_compact"),
    };
  });
  check("rail: compactar (68px + offset 68)",
    compact.body && compact.railW === 68 && compact.amMargin === "68px",
    JSON.stringify(compact));
  await page.screenshot({ path: shots + "l44-rail-compact.png" });

  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);
  const afterReload = await page.evaluate(() => {
    const rail = document.querySelector(".o_dolan_rail");
    const am = document.querySelector(".o_action_manager");
    return {
      body: document.body.classList.contains("dolan-compact"),
      railW: rail ? Math.round(rail.getBoundingClientRect().width) : null,
      amMargin: am ? getComputedStyle(am).marginLeft : null,
    };
  });
  check("rail: compact persiste tras reload",
    afterReload.body && afterReload.railW === 68 && afterReload.amMargin === "68px",
    JSON.stringify(afterReload));

  // volver a expandir (dejar estado inicial)
  await page.locator(".o_dolan_rail_toggle").click();
  await page.waitForTimeout(600);
  const expanded = await page.evaluate(() => {
    const rail = document.querySelector(".o_dolan_rail");
    const am = document.querySelector(".o_action_manager");
    return { body: document.body.classList.contains("dolan-compact"),
      railW: rail ? Math.round(rail.getBoundingClientRect().width) : null,
      amMargin: am ? getComputedStyle(am).marginLeft : null };
  });
  check("rail: expandir restaura 240px", !expanded.body && expanded.railW === 240 && expanded.amMargin === "240px",
    JSON.stringify(expanded));

  // ¿solapa contenido? (p.ej. vistas anchas, forms, board)
  await page.goto(`${BASE}/odoo/action-817`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);
  const overlap = await page.evaluate(() => {
    const rail = document.querySelector(".o_dolan_rail");
    const rr = rail ? rail.getBoundingClientRect().right : 0;
    const samples = [];
    for (const sel of [".o_control_panel", ".o_content", ".o_list_renderer", ".o_form_view", ".o_board_view", ".o_kanban_view", ".o_search_panel"]) {
      const el = document.querySelector(sel);
      if (el) { const r = el.getBoundingClientRect(); samples.push({ sel, x: Math.round(r.x), underRail: r.x < rr - 2 }); }
    }
    return { railRight: Math.round(rr), samples };
  });
  console.log("OVERLAP:", JSON.stringify(overlap));
  check("rail: no tapa el contenido", overlap.samples.every((s) => !s.underRail), JSON.stringify(overlap.samples));

  console.log("DESKTOP ERRS:", JSON.stringify([...new Set(errs)].slice(0, 6)));
  check("rail: 0 errores JS en desktop", errs.length === 0, `${errs.length} errores`);

  // escenario Inicio: sale del webclient a /dolan_apps (rail embebido, distinto)
  const inicio = page.locator('.o_dolan_rail_item[data-menu-xmlid="DOLAN_theme.menu_home_grid"]');
  if (await inicio.count()) {
    await inicio.click();
    await page.waitForTimeout(4000);
    const home = await page.evaluate(() => ({
      url: location.pathname,
      rails: document.querySelectorAll(".o_dolan_rail").length,
      hasVolver: [...document.querySelectorAll("a")].some((a) => /volver/i.test(a.textContent || "") && a.getAttribute("href") === "/odoo"),
      hasWebclient: !!document.querySelector(".o_main_navbar"),
      grid: document.querySelectorAll(".o_dolan_home_app").length,
      bodyPadLeft: getComputedStyle(document.body).paddingLeft,
      overflowX: document.documentElement.scrollWidth > window.innerWidth,
    }));
    console.log("INICIO:", JSON.stringify(home, null, 1));
    check("rail: Inicio abre la grilla sin rail embebida y con Volver",
      home.url === "/dolan_apps" && home.rails === 0 && home.hasVolver && home.grid > 0,
      JSON.stringify(home));
    await page.screenshot({ path: shots + "l44-rail-inicio-page.png" });
  } else {
    check("rail: item Inicio presente en el webclient", false, "DOLAN_theme.menu_home_grid no está en la rail");
  }
  await ctx.close();
}

// ---------- móvil ----------
{
  const { page, errs, ctx } = await newPage(390, 844);
  await page.goto(`${BASE}/web`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(6000);
  const mobile = await page.evaluate(() => {
    const rail = document.querySelector(".o_dolan_rail");
    const burger = document.querySelector(".o_menu_toggle, .o_burger_menu_toggle, [aria-label*='menú' i], [aria-label*='menu' i]");
    const am = document.querySelector(".o_action_manager");
    return {
      rail: !!rail,
      railVisible: rail ? rail.getBoundingClientRect().width > 0 : false,
      railDisplay: rail ? getComputedStyle(rail).display : null,
      burger: !!burger,
      amMargin: am ? getComputedStyle(am).marginLeft : null,
      overflowX: document.documentElement.scrollWidth > window.innerWidth,
      scrollW: document.documentElement.scrollWidth,
      innerW: window.innerWidth,
    };
  });
  console.log("MOBILE:", JSON.stringify(mobile));
  check("móvil: rail oculto", !mobile.railVisible && (mobile.railDisplay === "none" || !mobile.rail), JSON.stringify(mobile));
  check("móvil: sin scroll horizontal", !mobile.overflowX, `scrollW=${mobile.scrollW} innerW=${mobile.innerW}`);
  await page.screenshot({ path: shots + "l44-rail-mobile.png" });
  console.log("MOBILE ERRS:", JSON.stringify([...new Set(errs)].slice(0, 4)));
  await ctx.close();
}

await browser.close();
let failed = 0;
for (const r of results) { if (!r.ok) failed++; console.log(`${r.ok ? "PASS" : "FAIL"} | ${r.name} | ${r.detail}`); }
console.log(`\n${results.length - failed}/${results.length} checks OK`);
process.exit(failed ? 1 : 0);
