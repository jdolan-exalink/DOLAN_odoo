/** @odoo-module **/
// Grilla de apps "Inicio" DENTRO del webclient (estilo demo EE).
// Antes el Inicio era una act_url a /dolan_apps (página huérfana sin topbar);
// ahora es un client action: misma grilla, con la barra nativa de Odoo.
import { Component, onWillStart } from "@odoo/owl";

export class DolanHomeGrid extends Component {
    static template = "DOLAN_theme.HomeGrid";
    // Owl 3 (Odoo 20): sin static props; el componente no recibe props

    setup() {
        this.apps = [];
        onWillStart(async () => {
            try {
                // /web/webclient/load_menus es GET (rpc() manda POST y da 405)
                const res = await fetch("/web/webclient/load_menus", { credentials: "same-origin" })
                    .then((r) => r.json());
                const root = res.root || {};
                this.apps = (root.children || [])
                    .map((cid) => res[cid])
                    .filter((m) => m && m.appID === m.id);
            } catch {
                this.apps = [];
            }
        });
    }

    href(app) {
        // mismo criterio que la grilla standalone: actionPath si existe si no action-<id>
        return app.actionPath ? `/odoo/${app.actionPath}` : `/odoo/action-${app.actionID}`;
    }
}

// registro como client action (tag = id del registry)
import { registry } from "@web/core/registry";
registry.category("actions").add("dolan_theme.home_grid", DolanHomeGrid);
