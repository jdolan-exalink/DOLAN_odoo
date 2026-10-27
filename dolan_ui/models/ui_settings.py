from odoo import api, fields, models
from odoo.exceptions import UserError


class DolanUiSettings(models.TransientModel):
    _name = "dolan.ui.settings"
    _description = "Configuracion de apps Dolan (orden y por defecto)"

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
    default_app = fields.Many2one(
        "ir.ui.menu",
        string="App por defecto",
        domain="[('parent_id', '=', False), ('active', '=', True)]",
        help="App a la que entra el usuario despues del login.",
    )

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
        default_xmlid = params.get_str("dolan.ui.default_app", "")
        default_id = False
        if default_xmlid:
            rec = self.env.ref(default_xmlid, raise_if_not_found=False)
            default_id = rec.id if rec else False
        return {
            "app_order": ", ".join(order),
            "apps_help": "\n".join(order),
            "default_app": default_id,
            "tema": params.get_str("dolan.ui.tema", "auto"),
            "densidad": params.get_str("dolan.ui.densidad", "normal"),
            "widgets_order": params.get_str("dolan.ui.widgets",
                "facturas,compras,por_cobrar,nc,remitos,recepciones"),
        }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        defaults = self._load_defaults()
        for fname in ("app_order", "apps_help", "default_app", "tema", "densidad", "widgets_order"):
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
        if self.default_app:
            target = self.default_app
            # menus raiz no tienen accion: derivar al primer hijo con accion
            if not target.action:
                child = self.env["ir.ui.menu"].search(
                    [("parent_id", "=", target.id), ("active", "=", True),
                     ("action", "!=", False)], order="sequence", limit=1)
                if not child:
                    raise UserError(
                        "La app por defecto '%s' no tiene accion (elige un item hijo)." % target.name)
                target = child
            xid = self._menu_xmlid(target)
            if not xid:
                raise UserError("La app por defecto debe tener xmlid (menú de sistema).")
            params.set_str("dolan.ui.default_app", xid)
        else:
            params.set_str("dolan.ui.default_app", "")
        return True

    @api.model
    def get_public_config(self):
        def params_tema():
            return self.env["ir.config_parameter"].sudo().get_str("dolan.ui.tema", "auto")

        def params_densidad():
            return self.env["ir.config_parameter"].sudo().get_str("dolan.ui.densidad", "normal")

        """Para el JS del cliente: accion por defecto (referencia de menu)."""
        xid = self.env["ir.config_parameter"].sudo().get_str("dolan.ui.default_app", "")
        if not xid:
            return {"default_action": False, "default_menu_xmlid": False,
                    "tema": params_tema(), "densidad": params_densidad()}
        menu = self.env.ref(xid, raise_if_not_found=False)
        if not menu or not menu.action:
            return {"default_action": False, "default_menu_xmlid": False,
                    "tema": params_tema(), "densidad": params_densidad()}
        # Odoo20: menu.action devuelve recordset (p.ej. act_window(814,));
        # tambien acepta el formato string 'ir.actions.act_window,814'
        action = menu.action
        if not action:
            return {"default_action": False, "default_menu_xmlid": False,
                    "tema": params_tema(), "densidad": params_densidad()}
        if hasattr(action, "id"):
            return {"default_action": str(action.id) if action.id else False,
                    "default_menu_xmlid": xid,
                    "tema": params_tema(), "densidad": params_densidad()}
        action = str(action)
        if "," in action:
            action = action.split(",")[1]
        return {"default_action": action, "default_menu_xmlid": xid,
                "tema": params_tema(), "densidad": params_densidad()}
