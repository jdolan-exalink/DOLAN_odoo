/** @odoo-module **/

import { Component, onWillStart, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";

export class DolanDashboard extends Component {
    static template = "dolan_dash.DolanDashboard";
    // Owl 3 (Odoo 20): no static props; el componente no lee props

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        useBus(this.env.bus, "ACTION_MANAGER:UPDATE", () => this.refresh());
        // Owl 3 (Odoo 20): estado reactivo via proxy() (patron del core; useState ya no existe)
        this.state = proxy({ kpis: { company: "", mes: "", widgets: [] }, seccion: null, serie: null,
            detalle: { por_pagar: [], pagadas: [], facturas: [], nc: [], remitos: [], cheques: [] } });
        onWillStart(async () => {
            try {
                const [kpis, detalle] = await Promise.all([
                    this.orm.call("dolan.dash", "kpis", []),
                    this.orm.call("dolan.dash", "detalle", []),
                ]);
                this.state.kpis = kpis;
                this.state.detalle = detalle;
            } catch {
                this.state.kpis = { company: "", mes: "", widgets: [] };
                this.state.detalle = { por_pagar: [], pagadas: [], facturas: [], nc: [], remitos: [], cheques: [] };
            }
        });
    }

    open(xmlid) {
        this.action.doAction(xmlid);
    }

    /** Click en tarjeta: activa/desactiva la seccion y trae su grafico */
    async setSeccion(nombre) {
        if (this.state.seccion === nombre) {
            this.state.seccion = null;
            this.state.serie = null;
            return;
        }
        this.state.seccion = nombre;
        this.state.serie = null;
        try {
            this.state.serie = await this.orm.call("dolan.dash", "serie", [nombre]);
        } catch {
            this.state.serie = null;
        }
    }

    /** Refrescar KPIs + detalle + serie activa */
    async refresh() {
        try {
            const [kpis, detalle] = await Promise.all([
                this.orm.call("dolan.dash", "kpis", []),
                this.orm.call("dolan.dash", "detalle", []),
            ]);
            this.state.kpis = kpis;
            this.state.detalle = detalle;
            if (this.state.seccion) {
                this.state.serie = await this.orm.call("dolan.dash", "serie", [this.state.seccion]);
            }
        } catch { /* mantener estado anterior */ }
    }

    /** Registrar pago: wizard nativo de Odoo sobre la factura elegida */
    pagar(moveId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "account.payment.register",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
            context: { active_model: "account.move", active_ids: [moveId] },
        });
    }
}

registry.category("actions").add("dolan_dash.dashboard", DolanDashboard);
