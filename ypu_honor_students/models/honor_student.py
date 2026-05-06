from odoo import api, fields, models


class YpuHonorStudent(models.Model):
    _name = 'ypu.honor.student'
    _description = 'Honor Student'
    _order = 'sequence, name'

    name = fields.Char(required=True, string='Student Name')
    image_1920 = fields.Image('Photo', max_width=512, max_height=512)
    student_number = fields.Char(string='Student Number')
    faculty_id = fields.Many2one(
        'ypu.honor.faculty',
        string='Faculty',
        required=True,
        ondelete='restrict',
        index=True,
    )
    year_id = fields.Many2one(
        'ypu.honor.year',
        string='Year',
        ondelete='restrict',
        index=True,
    )
    study_year_id = fields.Many2one(
        'ypu.honor.study.year',
        string='Study Year',
        required=True,
        ondelete='restrict',
        index=True,
    )
    semester = fields.Selection(
        selection=[
            ('1', 'Semester 1'),
            ('2', 'Semester 2'),
            ('3', 'Semester 3'),
        ],
        string='Semester',
        required=True,
        default='1',
        index=True,
    )
    gpa = fields.Float(string='GPA', digits=(4, 2))
    honor_title = fields.Char(
        string='Honor Title',
        help='Optional label shown on the website card, e.g. "Top 10".',
    )
    achievement = fields.Text(string='Achievement Summary')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)
    website_published = fields.Boolean(string='Publish on Website', default=True)
    is_public = fields.Boolean(
        string='Publicly Visible',
        default=True,
        help='When disabled, this student is hidden from public website snippets.',
    )

    year_label = fields.Char(compute='_compute_year_label', string='Year Label')
    study_year_label = fields.Char(compute='_compute_study_year_label', string='Study Year Label')
    semester_label = fields.Char(compute='_compute_semester_label', string='Semester Label')

    @api.depends('year_id')
    def _compute_year_label(self):
        for rec in self:
            rec.year_label = rec.year_id.name or ''

    @api.depends('study_year_id', 'study_year_id.name')
    def _compute_study_year_label(self):
        for rec in self:
            rec.study_year_label = rec.study_year_id.name or ''

    @api.depends('semester')
    def _compute_semester_label(self):
        sem_map = dict(self._fields['semester'].selection)
        for rec in self:
            rec.semester_label = sem_map.get(rec.semester, '')

    @api.model
    def website_search_domain(
        self,
        search='',
        faculty_id=False,
        year_id=False,
        study_year=False,
        semester=False,
    ):
        domain = [
            ('active', '=', True),
            ('website_published', '=', True),
            ('is_public', '=', True),
        ]
        if faculty_id:
            try:
                faculty_id = int(faculty_id)
            except (TypeError, ValueError):
                faculty_id = False
            if faculty_id:
                domain.append(('faculty_id', '=', faculty_id))
        if year_id:
            try:
                year_id = int(year_id)
            except (TypeError, ValueError):
                year_id = False
            if year_id:
                domain.append(('year_id', '=', year_id))
        if study_year:
            try:
                study_year_id = int(study_year)
            except (TypeError, ValueError):
                study_year_id = False
            if study_year_id:
                domain.append(('study_year_id', '=', study_year_id))
        if semester:
            domain.append(('semester', '=', str(semester)))
        if search:
            domain += [
                '|', '|',
                ('name', 'ilike', search),
                ('student_number', 'ilike', search),
                ('honor_title', 'ilike', search),
            ]
        return domain
