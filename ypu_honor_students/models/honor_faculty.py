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
        Student = self.env['ypu.honor.student']
        for rec in self:
            rec.student_count = Student.search_count([
                ('faculty_id', '=', rec.id),
            ])
