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
    study_year = fields.Selection(
        selection=[
            ('1', 'Year 1'),
            ('2', 'Year 2'),
            ('3', 'Year 3'),
            ('4', 'Year 4'),
            ('5', 'Year 5'),
        ],
        string='Study Year',
        required=True,
        default='1',
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

    year_label = fields.Char(compute='_compute_labels', string='Year Label')
    semester_label = fields.Char(compute='_compute_labels', string='Semester Label')

    @api.depends('study_year', 'semester')
    def _compute_labels(self):
        year_map = dict(self._fields['study_year'].selection)
        sem_map = dict(self._fields['semester'].selection)
        for rec in self:
            rec.year_label = year_map.get(rec.study_year, '')
            rec.semester_label = sem_map.get(rec.semester, '')

    @api.model
    def website_search_domain(
        self,
        search='',
        faculty_id=False,
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
        if study_year:
            domain.append(('study_year', '=', str(study_year)))
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
