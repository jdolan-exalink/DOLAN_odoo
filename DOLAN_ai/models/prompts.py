"""Prompts predeterminados funcionales (reportes periódicos) por agente."""
from odoo import fields, models, _


class DolanAiAgente(models.Model):
    _inherit = "dolan.ai.agente"

    prompts_ids = fields.One2many("dolan.ai.prompt", "agente_id", string="Prompts predeterminados")


class DolanAiPrompt(models.Model):
    _name = "dolan.ai.prompt"
    _description = "Prompt predeterminado funcional"
    _order = "sequence, id"

    agente_id = fields.Many2one("dolan.ai.agente", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Nombre (chip)", required=True)
    prompt = fields.Text(string="Prompt", required=True)
    activo = fields.Boolean(default=True)
