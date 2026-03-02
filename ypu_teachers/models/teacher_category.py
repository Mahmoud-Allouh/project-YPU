from odoo import fields, models


class YpuTeacherCategory(models.Model):
    _name = 'ypu.teacher.category'
    _description = 'Teacher Category'
    _order = 'sequence, name'

    name = fields.Char(required=True, string="Name")
    description = fields.Text(string="Description")
    sequence = fields.Integer(default=10, string="Sequence")
    active = fields.Boolean(default=True, string="Active")
    teacher_count = fields.Integer(
        string="# Teachers",
        compute='_compute_teacher_count',
    )

    def _compute_teacher_count(self):
        grouped = self.env['ypu.teacher'].read_group(
            [('category_id', 'in', self.ids)],
            ['category_id'],
            ['category_id'],
        )
        count_map = {g['category_id'][0]: g['category_id_count'] for g in grouped}
        for rec in self:
            rec.teacher_count = count_map.get(rec.id, 0)
