from odoo import api, fields, models


class DolanBancoAr(models.Model):
    """Catalogo de bancos argentinos.

    En Odoo 20 el core elimino res.bank (y base_bank), por lo que el listado
    de ADHOC (l10n_ar_bank) no puede instalarse. Este catalogo propio (LGPL)
    reemplaza esa necesidad con nombre + codigo de entidad del BCRA.
    """

    _name = "dolan.banco.ar"
    _description = "Banco argentino (catalogo propio)"
    _order = "code, name"

    name = fields.Char(string="Banco", required=True)
    code = fields.Char(string="Codigo BCRA", size=3, index=True)
    city = fields.Char(string="Ciudad")
    country_id = fields.Many2one("res.country", string="Pais", default=lambda self: self.env.ref("base.ar"))
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_uniq", "unique(code)", "El codigo del banco debe ser unico."),
    ]

    @api.model
    def name_get(self):
        return [(b.id, "%s%s" % (b.name, " (%s)" % b.code if b.code else "")) for b in self]
