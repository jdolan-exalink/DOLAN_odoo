/** @odoo-module **/
// Atajos globales estilo Gmail: g + letra. Navegan con el servicio oficial
// `menu` (selectMenu) — mismo camino que un click de usuario, sin tocar el DOM.
import { registry } from "@web/core/registry";

const TECLAS = {
    o: "dolan_dash.menu_operaciones_root",
    h: "dolan_dash.menu_operaciones_root",
    v: "sale.sale_menu_root",
    c: "purchase.menu_purchase_root",
    i: "stock.menu_stock_root",
    f: "account.menu_finance",
    e: "contacts.menu_contacts",
    r: "crm.crm_menu_root",
    p: "point_of_sale.menu_point_root",
};

function esEditable(el) {
    return !!el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable);
}

registry.category("services").add("dolan_hotkeys", {
    dependencies: ["menu"],
    start(env, { menu }) {
        let pendiente = false;
        document.addEventListener("keydown", (ev) => {
            if (ev.ctrlKey || ev.metaKey || ev.altKey || esEditable(document.activeElement)) {
                return;
            }
            const key = (ev.key || "").toLowerCase();
            if (key === "g") {
                pendiente = true;
                window.clearTimeout(window.__dolanG);
                window.__dolanG = window.setTimeout(() => { pendiente = false; }, 1600);
                return;
            }
            if (!pendiente) {
                return;
            }
            pendiente = false;
            window.clearTimeout(window.__dolanG);
            const xmlid = TECLAS[key];
            if (!xmlid) {
                return;
            }
            const root = menu.getMenu("root");
            const target = (root?.children || [])
                .map((id) => menu.getMenu(id))
                .find((m) => m && m.xmlid === xmlid);
            if (target) {
                menu.selectMenu(target);
            }
        }, true);
    },
});
