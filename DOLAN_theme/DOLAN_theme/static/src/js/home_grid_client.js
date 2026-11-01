/** @odoo-module **/
// F3 — PRD04: role workspace inside the webclient (apps + KPIs + alerts +
// pending tasks + quick actions). Odoo 20 = Owl 3: no useState; plain fields
// are fine because onWillStart resolves before the first render.
import { Component, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

export class DolanHomeGrid extends Component {
    static template = "DOLAN_theme.HomeGrid";
    // Owl 3 (Odoo 20): sin static props; el componente no recibe props

    setup() {
        this.menu = useService("menu");
        this.apps = [];
        this.ctx = { role: "", role_label: "", kpis: [], alerts: [], tasks: [], quick_actions: [] };
        onWillStart(async () => {
            // apps: /web/webclient/load_menus es GET (rpc() manda POST y da 405)
            try {
                const res = await fetch("/web/webclient/load_menus", { credentials: "same-origin" })
                    .then((r) => r.json());
                const root = res.root || {};
                this.apps = (root.children || [])
                    .map((cid) => res[cid])
                    .filter((m) => m && m.appID === m.id);
            } catch {
                this.apps = [];
            }
            try {
                this.ctx = await rpc("/dolan/home_context", {});
            } catch {
                /* sin contexto: la grilla sigue funcionando sola */
            }
        });
    }

    href(app) {
        return app.actionPath ? `/odoo/${app.actionPath}` : `/odoo/action-${app.actionID}`;
    }

    goQuick(q) {
        const root = this.menu.getMenu("root");
        const target = (root?.children || [])
            .map((id) => this.menu.getMenu(id))
            .find((m) => m && m.xmlid === q.xmlid);
        if (target) { this.menu.selectMenu(target); }
    }

    openSearch() {
        try {
            this.env.services.dolan_global_search.open();
        } catch { /* servicio no cargado */ }
    }

    alertIcon(tone) {
        return tone === "critico" ? "exclamation-critical" : tone === "accion" ? "exclamation" : "info";
    }
}

registry.category("actions").add("dolan_theme.home_grid", DolanHomeGrid);
