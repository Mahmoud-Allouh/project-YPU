from odoo import fields, models


class YpuHonorStudyYear(models.Model):
    _name = 'ypu.honor.study.year'
    _description = 'Honor Student Study Year'
    _order = 'sequence, code, name'

    name = fields.Char(required=True, string='Study Year Name')
    code = fields.Char(required=True, string='Code', index=True)
    sequence = fields.Integer(default=10, string='Sequence')
    active = fields.Boolean(default=True, string='Active')
    student_count = fields.Integer(
        string='# Honor Students',
        compute='_compute_student_count',
    )

    _code_uniq = models.Constraint(
        'unique(code)',
        'A study year with the same code already exists.',
    )

    def _compute_student_count(self):
        Student = self.env['ypu.honor.student']
        for rec in self:
            rec.student_count = Student.search_count([
                ('study_year_id', '=', rec.id),
            ])
