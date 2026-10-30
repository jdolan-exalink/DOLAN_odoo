/** @odoo-module **/
// Toggle claro/oscuro en el systray — SIN import dinámico (rompe el bundle).
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";

export class ThemeToggle extends Component {
    static template = "DOLAN_theme.ThemeToggle";

    toggle() {
        const root = document.documentElement;
        const current = root.dataset.dolanTheme === "dark" ? "dark" : "light";
        const next = current === "dark" ? "light" : "dark";
        root.dataset.dolanTheme = next;
        this._apply(next);
        // The toggle is a per-browser preference; the server config remains the default.
        try {
            window.localStorage.setItem("dolan_theme_mode", next);
        } catch (_error) {
            // Private browsing policies may disable local storage; the current page still updates.
        }
    }
    _apply(mode) {
        const dark = mode === "dark";
        const vars = dark ? {
            "--o-dolan-bg": "#1a1a2e",
            "--o-dolan-surface": "#2a2a4a",
            "--o-dolan-surface2": "#1e1e3a",
            "--o-dolan-hover": "#2a2a4a",
            "--o-dolan-soft": "#2a2a4a",
            "--o-dolan-tx": "#e2e8f0",
            "--o-dolan-tx-mut": "#94a3b8",
            "--o-dolan-bd": "#40406a",
            "--o-dolan-pri": "#a67d8e",
            "--o-dolan-pri-dark": "#c4b5fd",
            "--o-dolan-pri-soft": "rgba(113,75,103,.25)",
            "--o-dolan-shadow": "0 1px 2px rgba(0,0,0,.2), 0 8px 24px rgba(0,0,0,.15)",
        } : null;
        if (dark) {
            for (const [k, v] of Object.entries(vars)) {
                document.documentElement.style.setProperty(k, v);
            }
        } else {
            for (const k of ["--o-dolan-bg","--o-dolan-surface","--o-dolan-surface2","--o-dolan-hover",
                            "--o-dolan-soft","--o-dolan-tx","--o-dolan-tx-mut","--o-dolan-bd",
                            "--o-dolan-pri","--o-dolan-pri-dark","--o-dolan-pri-soft","--o-dolan-shadow"]) {
                document.documentElement.style.removeProperty(k);
            }
        }
    }
}

registry.category("systray").add("dolan_theme.toggle", { Component: ThemeToggle }, { sequence: 8 });
