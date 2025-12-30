# -*- coding: utf-8 -*-
from odoo import fields, models


class YpuTeacherPosition(models.Model):
    _name = 'ypu.teacher.position'
    _description = 'Teacher Position'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
