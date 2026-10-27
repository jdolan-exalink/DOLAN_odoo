/** @odoo-module **/
// Sidebar compacta de DOLAN_theme: logica DOM pura (sin parches de componentes OWL).
import { registry } from "@web/core/registry";

const KEY = "dolan_rail_compact";

function applyCompact() {
    const compact = localStorage.getItem(KEY) === "1";
    document.body.classList.toggle("dolan-compact", compact);
    document.querySelectorAll(".o_dolan_rail").forEach((rail) => {
        rail.classList.toggle("o_dolan_rail_compact", compact);
    });
}

registry.category("services").add("dolan_rail_toggle", {
    start() {
        document.addEventListener("click", (ev) => {
            const btn = ev.target.closest("[data-dolan-rail-toggle]");
            if (!btn) {
                return;
            }
            const rail = document.querySelector(".o_dolan_rail");
            if (!rail) {
                return;
            }
            const next = !rail.classList.contains("o_dolan_rail_compact");
            localStorage.setItem(KEY, next ? "1" : "0");
            applyCompact();
        }, true);
        // el rail se monta despues de cargar menus (re-render reactivo incluido)
        new MutationObserver(applyCompact).observe(document.body, {
            childList: true,
            subtree: true,
        });
        applyCompact();
    },
});
