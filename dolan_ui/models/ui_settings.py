from odoo import api, fields, models
from odoo.exceptions import UserError


class DolanUiSettings(models.TransientModel):
    _name = "dolan.ui.settings"
    _description = "Configuracion de apps Dolan (orden)"

    app_order = fields.Char(
        string="Orden de apps (xmlids separados por coma)",
        help="Lista completa de apps de arriba hacia abajo. Edita el orden y aplica. "
             "El orden de la barra superior se actualiza al instante.",
    )
    apps_help = fields.Text(string="Apps disponibles (en el orden actual)", readonly=True)
    tema = fields.Selection(
        [("auto", "Automático (sistema)"), ("claro", "Claro"), ("oscuro", "Oscuro")],
        string="Tema", default="auto")
    densidad = fields.Selection(
        [("cozy", "Cómoda"), ("normal", "Normal"), ("compact", "Compacta")],
        string="Densidad", default="normal")
    widgets_order = fields.Char(
        string="Widgets del Home (orden, sin usar = oculto)",
        help="Ej: facturas,compras,por_cobrar,nc,remitos,recepciones")

    @api.model
    def _top_menus(self):
        return self.env["ir.ui.menu"].search([("parent_id", "=", False), ("active", "=", True)])

    @api.model
    def _menu_xmlid(self, menu):
        d = self.env["ir.model.data"].search(
            [("model", "=", "ir.ui.menu"), ("res_id", "=", menu.id)], limit=1)
        return f"{d.module}.{d.name}" if d else False

    @api.model
    def _load_defaults(self):
        params = self.env["ir.config_parameter"].sudo()
        stored = params.get_str("dolan.ui.app_order", "")
        if stored:
            order = [x.strip() for x in stored.split(",") if x.strip()]
        else:
            order = [self._menu_xmlid(m) or str(m.id) for m in self._top_menus()]
        return {
            "app_order": ", ".join(order),
            "apps_help": "\n".join(order),
            "tema": params.get_str("dolan.ui.tema", "auto"),
            "densidad": params.get_str("dolan.ui.densidad", "normal"),
            "widgets_order": params.get_str("dolan.ui.widgets",
                "facturas,compras,por_cobrar,nc,remitos,recepciones"),
        }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        defaults = self._load_defaults()
        for fname in ("app_order", "apps_help", "tema", "densidad", "widgets_order"):
            if fname in fields_list:
                res[fname] = defaults[fname]
        return res

    def action_apply(self):
        self.ensure_one()
        tokens = [t.strip() for t in (self.app_order or "").split(",") if t.strip()]
        if not tokens:
            raise UserError("El orden no puede estar vacio.")
        menus = self._top_menus()
        by_xmlid = {}
        for m in menus:
            xid = self._menu_xmlid(m)
            if xid:
                by_xmlid[xid] = m
        by_id = {str(m.id): m for m in menus}
        ordered, seen = [], set()
        for tok in tokens:
            menu = by_xmlid.get(tok) or by_id.get(tok)
            if not menu:
                raise UserError(
                    "App desconocida en el orden: '%s'.\nDisponibles:\n%s"
                    % (tok, ", ".join(sorted(by_xmlid))))
            if menu.id in seen:
                raise UserError("App duplicada en el orden: '%s'" % tok)
            seen.add(menu.id)
            ordered.append(menu)
        # las que no vinieron en la lista quedan al final, en su orden actual
        for m in menus:
            if m.id not in seen:
                ordered.append(m)
        for idx, menu in enumerate(ordered):
            menu.sequence = (idx + 1) * 10

        params = self.env["ir.config_parameter"].sudo()
        params.set_str("dolan.ui.app_order", ", ".join(
            self._menu_xmlid(m) or str(m.id) for m in ordered))
        params = self.env["ir.config_parameter"].sudo()
        params.set_str("dolan.ui.tema", self.tema or "auto")
        params.set_str("dolan.ui.densidad", self.densidad or "normal")
        params.set_str("dolan.ui.widgets",
                       (self.widgets_order or "").replace(" ", ""))
        return True

    @api.model
    def get_public_config(self):
        """Config publica para el cliente (tema/densidad).

        La entrada la decide Odoo: restaura la ultima app de la sesion o abre
        la primera del orden. No hay accion por defecto propia (S7).
        """
        params = self.env["ir.config_parameter"].sudo()
        return {
            "tema": params.get_str("dolan.ui.tema", "auto"),
            "densidad": params.get_str("dolan.ui.densidad", "normal"),
        }
