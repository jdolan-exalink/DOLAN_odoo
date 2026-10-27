/** @odoo-module **/
// Aplica tema (claro/oscuro/auto) y densidad desde la config de dolan_ui.
import { registry } from "@web/core/registry";
import { useBus } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

function resolverTema(tema) {
    if (tema === "auto" || !tema) {
        return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark" : "light";
    }
    return tema === "oscuro" ? "dark" : "light";
}

function aplicar(cfg) {
    if (!cfg) return;
    document.documentElement.dataset.dolanTheme = resolverTema(cfg.tema);
    if (cfg.densidad && cfg.densidad !== "normal") {
        document.documentElement.dataset.dolanDensity = cfg.densidad;
    } else {
        delete document.documentElement.dataset.dolanDensity;
    }
}

registry.category("services").add("dolan_theme_apply", {
    start(env) {
        rpc("/web/dolan_ui/config").then(aplicar).catch(() => {});
        if (env.bus && env.bus.addEventListener) {
            env.bus.addEventListener("ACTION_MANAGER:UPDATE", () => {
                rpc("/web/dolan_ui/config").then(aplicar).catch(() => {});
            });
        } else if (env.bus && env.bus.on) {
            env.bus.on("ACTION_MANAGER:UPDATE", null, () => {
                rpc("/web/dolan_ui/config").then(aplicar).catch(() => {});
            });
        }
    },
});
