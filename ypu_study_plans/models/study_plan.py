import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class YpuStudyPlan(models.Model):
    _name = 'ypu.study.plan'
    _description = 'Study Plan'
    _order = 'sequence, name'

    name = fields.Char(string='Plan Name', required=True, translate=True)
    code = fields.Char(
        string='Code',
        help='Short unique identifier used to reference this plan from URLs or snippets.',
        copy=False,
    )
    subtitle = fields.Char(string='Subtitle', translate=True)
    description = fields.Html(string='Description', translate=True, sanitize=False)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    section_ids = fields.One2many(
        'ypu.study.plan.section', 'plan_id', string='Sections', copy=True,
    )
    section_count = fields.Integer(compute='_compute_counts')
    course_count = fields.Integer(compute='_compute_counts')
    total_credit_hours = fields.Float(
        string='Total Credits', compute='_compute_counts', digits=(8, 2),
    )

    _code_uniq = models.Constraint(
        'unique(code)',
        'A study plan with the same code already exists.',
    )

    @api.depends('section_ids', 'section_ids.course_ids', 'section_ids.course_ids.credit_hours')
    def _compute_counts(self):
        for rec in self:
            rec.section_count = len(rec.section_ids)
            courses = rec.section_ids.mapped('course_ids')
            rec.course_count = len(courses)
            rec.total_credit_hours = sum(courses.mapped('credit_hours'))

    @api.constrains('code')
    def _check_code(self):
        for rec in self:
            if rec.code and not re.match(r'^[A-Za-z0-9_\-]+$', rec.code):
                raise ValidationError(_(
                    "Code can only contain letters, digits, underscores and hyphens."
                ))

    def copy(self, default=None):
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _('%s (copy)') % self.name
        if 'code' not in default and self.code:
            default['code'] = False
        return super().copy(default)
