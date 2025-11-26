# -*- coding: utf-8 -*-
from odoo import api, fields, models


class YpuTeacherCategory(models.Model):
    _name = 'ypu.teacher.category'
    _description = 'Teacher Category'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    description = fields.Text()
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    teacher_count = fields.Integer(compute='_compute_teacher_count')

    def _compute_teacher_count(self):
        grouped = self.env['ypu.teacher'].read_group(
            [('category_id', 'in', self.ids)],
            ['category_id'],
            ['category_id'],
        )
        count_map = {g['category_id'][0]: g['category_id_count'] for g in grouped}
        for category in self:
            category.teacher_count = count_map.get(category.id, 0)
