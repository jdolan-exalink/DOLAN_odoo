/** @odoo-module **/
// F6 — PRD04: light UX metrics instrumentation (clicks, locally stored ring
// buffer). Reporting vs the Odoo CE baseline comes in a later slice.
import { registry } from "@web/core/registry";

const MAX = 300;

function push(entry) {
    let items;
    try { items = JSON.parse(localStorage.getItem("dolan_ux_metrics") || "[]"); } catch { items = []; }
    items.push(entry);
    if (items.length > MAX) { items = items.slice(-MAX); }
    try { localStorage.setItem("dolan_ux_metrics", JSON.stringify(items)); } catch { /* quota */ }
}

registry.category("services").add("dolan_ux_metrics", {
    start() {
        document.addEventListener("click", (ev) => {
            const el = ev.target && ev.target.closest
                ? ev.target.closest("button, a, .o_data_row, .o_dolan_home_app") : null;
            if (!el) return;
            push({
                t: Date.now(),
                type: "click",
                target: (el.className || el.tagName || "").toString().slice(0, 60),
                path: (location.pathname || "").slice(0, 60),
            });
        }, true);
        return {
            snapshot: () => { try { return JSON.parse(localStorage.getItem("dolan_ux_metrics") || "[]"); } catch { return []; } },
            clear: () => { try { localStorage.removeItem("dolan_ux_metrics"); } catch { /* */ } },
        };
    },
});
