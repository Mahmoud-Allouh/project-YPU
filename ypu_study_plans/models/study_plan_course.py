from odoo import fields, models


class YpuStudyPlanCourse(models.Model):
    _name = 'ypu.study.plan.course'
    _description = 'Study Plan Course'
    _order = 'sequence, id'

    section_id = fields.Many2one(
        'ypu.study.plan.section', string='Section',
        required=True, ondelete='cascade', index=True,
    )
    plan_id = fields.Many2one(
        'ypu.study.plan', related='section_id.plan_id', store=True, index=True,
    )
    sequence = fields.Integer(default=10)

    code = fields.Char(string='Course Code', help='e.g. URQ 121')
    name_ar = fields.Char(string='Course Name (Arabic)', translate=True)
    name_en = fields.Char(string='Course Name (English)', translate=True)

    theory_hours = fields.Float(string='Theory Hours', digits=(4, 2))
    practical_hours = fields.Float(string='Practical Hours', digits=(4, 2))
    credit_hours = fields.Float(string='Credit Hours (CH)', digits=(4, 2))

    prerequisite = fields.Char(
        string='Prerequisite',
        help='Free-text prerequisite (e.g. "URQ 211" or "End of remedial English").',
    )
    description = fields.Text(string='Description', translate=True)

    display_name_combined = fields.Char(
        compute='_compute_display_name_combined', store=False,
    )

    def _compute_display_name_combined(self):
        for rec in self:
            parts = [p for p in (rec.code, rec.name_ar or rec.name_en) if p]
            rec.display_name_combined = ' - '.join(parts) if parts else ''
