from odoo import fields, models


class YpuTeacherPosition(models.Model):
    _name = 'ypu.teacher.position'
    _description = 'Teacher Position'
    _order = 'sequence, name'

    name = fields.Char(required=True, string="Name")
    sequence = fields.Integer(default=10, string="Sequence")
    active = fields.Boolean(default=True, string="Active")
