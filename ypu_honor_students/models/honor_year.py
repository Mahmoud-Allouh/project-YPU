from odoo import fields, models


class YpuHonorYear(models.Model):
    _name = 'ypu.honor.year'
    _description = 'Honor Student Year'
    _order = 'sequence, code, name'

    name = fields.Char(required=True, string='Year Name')
    code = fields.Selection(
        selection=[
            ('1', 'Year 1'),
            ('2', 'Year 2'),
            ('3', 'Year 3'),
            ('4', 'Year 4'),
            ('5', 'Year 5'),
        ],
        required=True,
        string='Code',
        default='1',
        index=True,
    )
    sequence = fields.Integer(default=10, string='Sequence')
    active = fields.Boolean(default=True, string='Active')
    student_count = fields.Integer(
        string='# Honor Students',
        compute='_compute_student_count',
    )

    _code_uniq = models.Constraint(
        'unique(code)',
        'A year with the same code already exists.',
    )

    def _compute_student_count(self):
        Student = self.env['ypu.honor.student']
        for rec in self:
            rec.student_count = Student.search_count([
                ('year_id', '=', rec.id),
            ])
