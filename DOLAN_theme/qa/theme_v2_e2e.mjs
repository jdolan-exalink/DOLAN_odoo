import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const baseURL = process.env.ODOO_URL || "http://localhost:8070";
const db = process.env.ODOO_DB || "dolan";
const login = process.env.ODOO_LOGIN;
const password = process.env.ODOO_PASSWORD;
const themeRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));
const evidenceDir = process.env.THEME_EVIDENCE_DIR
    ? resolve(process.env.THEME_EVIDENCE_DIR)
    : resolve(themeRoot, "docs/evidence/theme-v2-local");
if (!login || !password) throw new Error("Set ODOO_LOGIN and ODOO_PASSWORD in the environment.");

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1440, height: 950 } });
const page = await context.newPage();
const pageErrors = [];
page.on("pageerror", (error) => pageErrors.push(error.message));

try {
    const auth = await page.request.post(`${baseURL}/web/session/authenticate`, {
        data: { jsonrpc: "2.0", params: { db, login, password } },
    });
    const authResult = await auth.json();
    if (!auth.ok() || !authResult.result?.uid) throw new Error("Odoo authentication failed.");

    await page.goto(`${baseURL}/web`, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".o_dolan_theme_toggle", { timeout: 30000 });
    if (await page.locator(".modal").count()) throw new Error("Odoo displayed a client error modal on startup.");

    const nativeAppsButton = page.locator(".o_navbar_apps_menu button");
    await nativeAppsButton.click();
    const nativeAppsMenu = page.locator(".o-dropdown--menu:has(.o_app)");
    await nativeAppsMenu.waitFor({ state: "visible" });
    const dropdownApps = await nativeAppsMenu.locator(".o_app").count();
    if (dropdownApps < 1) throw new Error("The native Odoo apps dropdown did not render its app entries.");
    await page.keyboard.press("Escape");
    console.log(`PASS: native apps dropdown opens with ${dropdownApps} authorized apps.`);

    await page.locator(".o_dolan_theme_toggle").click();
    await page.waitForFunction(() => document.documentElement.dataset.dolanTheme === "dark");
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForFunction(() => document.documentElement.dataset.dolanTheme === "dark");
    await page.locator(".o_dolan_theme_toggle").click();
    await page.waitForFunction(() => document.documentElement.dataset.dolanTheme === "light");
    console.log("PASS: systray dark/light toggle persists across reload.");

    const homeMenu = page.locator('[data-menu-xmlid="DOLAN_theme.menu_home_grid"]');
    if (await homeMenu.count() !== 1) throw new Error("The Inicio menu is missing from the native navigation rail.");
    await homeMenu.click();
    await page.waitForURL("**/dolan_apps");
    await page.waitForSelector("#apps-grid");
    const homeState = await page.evaluate(() => ({
        rails: document.querySelectorAll(".o_dolan_rail").length,
        back: [...document.querySelectorAll("a")].some((a) => a.getAttribute("href") === "/odoo" && /volver/i.test(a.textContent || "")),
    }));
    if (homeState.rails !== 0 || !homeState.back) {
        throw new Error(`Home grid must have no embedded rail and a back link: ${JSON.stringify(homeState)}`);
    }
    console.log("PASS: native Inicio menu opens the standalone home grid (no embedded sidebar, back link present).");

    await page.goto(`${baseURL}/dolan_apps`, { waitUntil: "domcontentloaded" });
    const grid = page.locator(".o_dolan_home_app");
    await page.waitForFunction(() => document.querySelectorAll(".o_dolan_home_app").length > 0);
    const gridInfo = await page.evaluate(() => {
        const icon = document.querySelector(".icon_wrap img");
        const links = [...document.querySelectorAll(".o_dolan_home_app")];
        return {
            apps: links.length,
            iconWidth: icon ? Math.round(icon.getBoundingClientRect().width) : 0,
            linksValid: links.every((link) => link.href.startsWith(`${location.origin}/odoo/`)),
            toggle: Boolean(document.querySelector("#theme-toggle")),
        };
    });
    if (gridInfo.apps < 1 || gridInfo.iconWidth !== 70 || !gridInfo.linksValid || !gridInfo.toggle) {
        throw new Error(`Home grid validation failed: ${JSON.stringify(gridInfo)}`);
    }
    await mkdir(evidenceDir, { recursive: true });
    await page.screenshot({ path: resolve(evidenceDir, "home-grid-light.png") });
    const firstAppHref = await grid.first().getAttribute("href");
    await grid.first().click();
    await page.waitForURL((url) => url.pathname.startsWith("/odoo/"));
    if (!firstAppHref) throw new Error("Home-grid app link is missing its Odoo route.");
    console.log("PASS: opening a grid app navigates into the Odoo webclient.");

    await page.goto(`${baseURL}/dolan_apps`, { waitUntil: "domcontentloaded" });
    await page.locator("#theme-toggle").click();
    await page.waitForFunction(() => document.documentElement.dataset.dolanTheme === "dark");
    await page.waitForFunction(() => getComputedStyle(document.querySelector(".name")).color === "rgb(226, 232, 240)");
    const darkColors = await page.evaluate(() => ({
        background: getComputedStyle(document.body).backgroundColor,
        label: getComputedStyle(document.querySelector(".name")).color,
        back: [...document.querySelectorAll("a")].some((a) => a.getAttribute("href") === "/odoo" && /volver/i.test(a.textContent || "")),
    }));
    if (darkColors.background !== "rgb(26, 26, 46)" || darkColors.label !== "rgb(226, 232, 240)" || !darkColors.back) {
        throw new Error(`Dark-mode contrast validation failed: ${JSON.stringify(darkColors)}`);
    }
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForFunction(() => document.documentElement.dataset.dolanTheme === "dark");
    await page.waitForFunction(() => getComputedStyle(document.querySelector(".name")).color === "rgb(226, 232, 240)");
    await page.screenshot({ path: resolve(evidenceDir, "home-grid-dark.png") });
    console.log(`PASS: home grid has ${gridInfo.apps} apps, 70px icons, valid Odoo links, and persistent dark mode.`);

    await grid.first().click();
    await page.waitForURL((url) => url.pathname.startsWith("/odoo/"));
    await page.waitForFunction(() => document.documentElement.dataset.dolanTheme === "dark");
    console.log("PASS: dark mode remains selected when entering an Odoo app.");

    await page.goto(`${baseURL}/dolan_apps`, { waitUntil: "domcontentloaded" });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.reload({ waitUntil: "domcontentloaded" });
    const mobile = await page.evaluate(() => ({
        width: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        gridPresent: Boolean(document.querySelector("#apps-grid")),
        toggleVisible: document.querySelector("#theme-toggle")?.getBoundingClientRect().width > 0,
    }));
    if (mobile.scrollWidth > mobile.width || !mobile.gridPresent || !mobile.toggleVisible) {
        throw new Error(`Mobile layout validation failed: ${JSON.stringify(mobile)}`);
    }
    console.log("PASS: mobile home grid fits the viewport and exposes the theme toggle.");

    if (pageErrors.length) throw new Error(`Browser errors: ${pageErrors.join(" | ")}`);
    console.log("PASS: no uncaught browser errors.");
} finally {
    await browser.close();
}
