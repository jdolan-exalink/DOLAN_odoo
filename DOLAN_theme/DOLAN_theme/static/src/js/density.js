/** @odoo-module **/
// F4 — PRD04: density toggle (normal/compact) persisted per browser.
// Ctrl+Alt+D cycles the mode; the body class drives productivity.scss.
import { registry } from "@web/core/registry";

const LS = "dolan_density";

function apply(mode) {
    try {
        document.body.classList.toggle("o_dolan_compact", mode === "compact");
    } catch { /* no body yet */ }
}

export const densityService = {
    start() {
        let mode = "normal";
        try { mode = localStorage.getItem(LS) === "compact" ? "compact" : "normal"; } catch { /* ignore */ }
        const set = (next) => {
            mode = next === "compact" ? "compact" : "normal";
            try { localStorage.setItem(LS, mode); } catch { /* ignore */ }
            apply(mode);
            return mode;
        };
        const init = () => apply(mode);
        if (document.body) { init(); } else { document.addEventListener("DOMContentLoaded", init, { once: true }); }
        document.addEventListener("keydown", (ev) => {
            if (ev.ctrlKey && ev.altKey && (ev.key === "d" || ev.key === "D")) {
                ev.preventDefault();
                set(mode === "compact" ? "normal" : "compact");
            }
        });
        return { get: () => mode, set };
    },
};

registry.category("services").add("dolan_density", densityService);
