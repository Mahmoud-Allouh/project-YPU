from odoo import fields, models


class YpuHonorFaculty(models.Model):
    _name = 'ypu.honor.faculty'
    _description = 'Honor Student Faculty'
    _order = 'sequence, name'

    name = fields.Char(required=True, string='Faculty Name')
    sequence = fields.Integer(default=10, string='Sequence')
    active = fields.Boolean(default=True, string='Active')
    student_count = fields.Integer(
        string='# Honor Students',
        compute='_compute_student_count',
    )

    def _compute_student_count(self):
        grouped = self.env['ypu.honor.student'].read_group(
            [('faculty_id', 'in', self.ids)],
            ['faculty_id'],
            ['faculty_id'],
        )
        count_map = {g['faculty_id'][0]: g['faculty_id_count'] for g in grouped}
        for rec in self:
            rec.student_count = count_map.get(rec.id, 0)
