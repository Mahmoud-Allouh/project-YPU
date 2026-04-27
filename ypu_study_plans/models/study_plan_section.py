from odoo import api, fields, models


class YpuStudyPlanSection(models.Model):
    _name = 'ypu.study.plan.section'
    _description = 'Study Plan Section'
    _order = 'sequence, id'

    plan_id = fields.Many2one(
        'ypu.study.plan', string='Plan', required=True, ondelete='cascade', index=True,
    )
    name = fields.Char(string='Section Title', required=True, translate=True)
    subtitle = fields.Char(
        string='Subtitle',
        help='Short helper line shown under the section title (e.g. "9 credit hours").',
        translate=True,
    )
    description = fields.Html(string='Description', translate=True, sanitize=False)
    sequence = fields.Integer(default=10)

    section_type = fields.Selection(
        [
            ('category', 'Category (e.g. University Requirements)'),
            ('semester', 'Semester (e.g. Year 1 - Term 1)'),
            ('elective', 'Elective Group'),
            ('custom', 'Custom'),
        ],
        string='Section Type', default='category',
    )
    show_total_row = fields.Boolean(
        string='Show Totals Row', default=True,
        help='Display a total row at the bottom summing the hours columns.',
    )
    show_description_column = fields.Boolean(
        string='Show Description Column', default=False,
        help='Add a "Description" column to the rendered table.',
    )
    show_prerequisite_column = fields.Boolean(
        string='Show Prerequisite Column', default=True,
    )

    course_ids = fields.One2many(
        'ypu.study.plan.course', 'section_id', string='Courses', copy=True,
    )

    course_count = fields.Integer(compute='_compute_totals')
    total_theory = fields.Float(compute='_compute_totals', digits=(8, 2))
    total_practical = fields.Float(compute='_compute_totals', digits=(8, 2))
    total_credit = fields.Float(compute='_compute_totals', digits=(8, 2))

    @api.depends(
        'course_ids', 'course_ids.theory_hours',
        'course_ids.practical_hours', 'course_ids.credit_hours',
    )
    def _compute_totals(self):
        for rec in self:
            rec.course_count = len(rec.course_ids)
            rec.total_theory = sum(rec.course_ids.mapped('theory_hours'))
            rec.total_practical = sum(rec.course_ids.mapped('practical_hours'))
            rec.total_credit = sum(rec.course_ids.mapped('credit_hours'))
