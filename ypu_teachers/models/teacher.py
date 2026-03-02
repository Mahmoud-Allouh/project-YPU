from odoo import api, fields, models


class YpuTeacher(models.Model):
    _name = 'ypu.teacher'
    _description = 'Teacher'
    _order = 'sequence, name'

    # ── Identity ─────────────────────────────────────────────
    name = fields.Char(required=True, string="Full Name")
    image_1920 = fields.Image("Photo", max_width=512, max_height=512)
    bio = fields.Html(string="Profile")

    # ── Academic info ────────────────────────────────────────
    department = fields.Char(string="Department")
    subject = fields.Char(string="Subject")
    rank = fields.Char(string="Rank")
    category_id = fields.Many2one(
        'ypu.teacher.category',
        string="Category",
        ondelete='set null',
        index=True,
    )
    position_id = fields.Many2one(
        'ypu.teacher.position',
        string="Position",
        ondelete='set null',
        index=True,
    )

    # ── Contact / links ──────────────────────────────────────
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    linkedin_url = fields.Char(string="LinkedIn URL")
    research_gate = fields.Char(string="Research Gate")

    # ── Website display ──────────────────────────────────────
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Controls the display order of teacher cards on the website.",
    )
    is_dean = fields.Boolean(string="Featured (Dean Card)", default=False)
    available = fields.Boolean(string="Available", default=True)
    website_published = fields.Boolean(string="Publish on Website", default=True)
    is_public = fields.Boolean(
        string="Publicly Visible",
        default=True,
        help="When disabled the teacher is hidden from the public listing.",
    )
    show_link_button = fields.Boolean(
        string="Show Link Button",
        default=False,
        help="Display an action button on the website card.",
    )
    link_url = fields.Char(
        string="Card Link URL",
        help="URL opened by the card action button.",
    )

    # ── Helpers ──────────────────────────────────────────────

    @api.model
    def website_search_domain(self, search='', category_id=False, available=None):
        """Return a domain suitable for the public teacher listing."""
        domain = [
            ('website_published', '=', True),
            ('is_public', '=', True),
        ]
        if search:
            domain += [
                '|', '|',
                ('name', 'ilike', search),
                ('subject', 'ilike', search),
                ('department', 'ilike', search),
            ]
        if category_id:
            domain.append(('category_id', '=', int(category_id)))
        if available is not None:
            domain.append(('available', '=', available))
        return domain
