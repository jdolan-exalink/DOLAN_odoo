from odoo import api, fields, models


class DolanWorkpaper(models.Model):
    """Archivos de trabajo (papeles de trabajo) del ciclo contable/auditoria.
    Equivalente propio (LGPL) del modulo EE account_workpapers: no copia
    codigo Enterprise."""

    _name = "dolan.workpaper"
    _description = "Archivo de trabajo"
    _order = "date_from desc, id desc"
    _rec_name = "title"

    title = fields.Char(string="Titulo", required=True)
    date_from = fields.Date(string="Desde")
    date_to = fields.Date(string="Hasta")
    account_id = fields.Many2one("account.account", string="Cuenta")
    partner_id = fields.Many2one("res.partner", string="Contacto")
    state = fields.Selection(
        selection=[("draft", "Borrador"), ("review", "En revision"), ("approved", "Aprobado")],
        string="Estado", default="draft", required=True, index=True)
    notes = fields.Text(string="Notas / conclusiones")
    user_id = fields.Many2one("res.users", string="Preparado por",
                              default=lambda self: self.env.user)
    reviewer_id = fields.Many2one("res.users", string="Revisado por")
    review_date = fields.Date(string="Fecha de revision")
    datas = fields.Binary(string="Archivo adjunto", attachment=True)
    datas_filename = fields.Char(string="Nombre del archivo")

    def action_review(self):
        self.write({"state": "review", "reviewer_id": self.env.user.id,
                    "review_date": fields.Date.context_today(self)})
        return True

    def action_approve(self):
        self.write({"state": "approved", "reviewer_id": self.env.user.id,
                    "review_date": fields.Date.context_today(self)})
        return True

    def action_draft(self):
        self.write({"state": "draft", "reviewer_id": False, "review_date": False})
        return True
