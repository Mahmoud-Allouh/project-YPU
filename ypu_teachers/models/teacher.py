import html as _html_lib
import re
import unicodedata

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
    google_scholar = fields.Char(string="Google Scholar URL")

    # ── CV ───────────────────────────────────────────────────
    cv_file = fields.Binary(string="CV (PDF)", attachment=True)
    cv_filename = fields.Char(string="CV Filename")
    cv_url = fields.Char(
        string="CV URL",
        help="External CV link, used if no CV file is uploaded.",
    )
    cv_download_url = fields.Char(
        string="CV Download Link", compute='_compute_cv_download_url',
    )

    @api.depends('cv_file', 'cv_url')
    def _compute_cv_download_url(self):
        for rec in self:
            if rec.cv_file:
                rec.cv_download_url = f'/web/content/ypu.teacher/{rec.id}/cv_file?download=true'
            elif rec.cv_url:
                rec.cv_download_url = rec.cv_url
            else:
                rec.cv_download_url = False

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
    website_slug = fields.Char(
        string="URL Slug",
        copy=False,
        index=True,
        help="Used for this teacher's profile page. Auto-generated from name.",
    )
    website_page_id = fields.Many2one(
        'website.page',
        string='Website Page',
        copy=False,
        ondelete='set null',
        index=True,
        help="The editable website page created for this teacher.",
    )

    # ── Profile page rich sections ───────────────────────────
    personal_info = fields.Html(
        string="Personal Information",
        help="Shown in the Personal Information tab on the profile page.",
    )
    contact_info = fields.Html(
        string="Contact Information (extra)",
        help="Additional contact details for the profile tab. Email/Phone are shown automatically.",
    )
    education = fields.Html(
        string="Education",
        help="Degrees, universities, years – shown in the Education tab.",
    )
    career = fields.Html(
        string="Career",
        help="Work history – shown in the Career tab.",
    )
    administration = fields.Html(
        string="Administration Roles",
        help="Administrative positions – shown in the Administration tab.",
    )
    supervising = fields.Html(
        string="Supervising",
        help="Thesis / project supervision – shown in the Supervising tab.",
    )
    publications = fields.Html(
        string="Publications",
        help="Research papers and publications – shown in the Publications tab.",
    )
    courses = fields.Html(
        string="Courses",
        help="Subjects taught – shown in the Courses tab.",
    )

    # ── Helpers ──────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            updates = {}
            if not rec.website_slug:
                slug = rec._make_unique_slug(self._slugify(rec.name))
                updates['website_slug'] = slug
            else:
                slug = rec.website_slug
            # Always auto-fill Card Link URL so the "View Profile" button is visible
            if not rec.link_url:
                updates['link_url'] = '/' + slug
            if updates:
                rec.write(updates)
        return records

    @api.onchange('name')
    def _onchange_name_slug(self):
        if self.name and not self.website_slug:
            self.website_slug = self._slugify(self.name)

    @staticmethod
    def _slugify(name):
        if not name:
            return ''
        s = unicodedata.normalize('NFKD', name)
        s = s.encode('ascii', 'ignore').decode('ascii')
        s = s.lower()
        s = re.sub(r'[^\w\s-]', '', s)
        s = re.sub(r'[\s_]+', '-', s.strip())
        return s.strip('-')

    def _make_unique_slug(self, base_slug):
        if not base_slug:
            base_slug = f'teacher-{self.id}'
        slug = base_slug
        counter = 2
        while self.search_count([('website_slug', '=', slug), ('id', '!=', self.id)]):
            slug = f'{base_slug}-{counter}'
            counter += 1
        return slug

    # ── Website page builder ──────────────────────────────────

    def _contact_html(self):
        """Build HTML for the Contact tab from structured fields."""
        e = _html_lib.escape
        parts = []
        if self.email:
            parts.append(
                f'<p class="lead">E-mail: '
                f'<a href="mailto:{e(self.email)}">{e(self.email)}</a></p>'
            )
        if self.linkedin_url:
            u = e(self.linkedin_url)
            parts.append(
                f'<p class="lead">LinkedIn: '
                f'<a href="{u}" target="_blank" rel="noopener noreferrer">{u}</a></p>'
            )
        if self.google_scholar:
            u = e(self.google_scholar)
            parts.append(
                f'<p class="lead">Google Scholar: '
                f'<a href="{u}" target="_blank" rel="noopener noreferrer">{u}</a></p>'
            )
        if self.research_gate:
            u = e(self.research_gate)
            parts.append(
                f'<p class="lead">Research Gate: '
                f'<a href="{u}" target="_blank" rel="noopener noreferrer">{u}</a></p>'
            )
        if self.contact_info:
            parts.append(str(self.contact_info))
        return '\n'.join(parts)

    def _build_page_arch(self):
        """Return arch XML for this teacher's website.page view (modern design)."""
        e = _html_lib.escape
        name_safe = e(self.name or '')

        # ── Photo ────────────────────────────────────────────────────
        if self.image_1920:
            image_html = (
                f'<img src="/web/image/ypu.teacher/{self.id}/image_1920" '
                f'alt="{name_safe}" loading="lazy" '
                f'style="width:260px;height:260px;object-fit:cover;border-radius:24px;'
                f'box-shadow:0 20px 60px rgba(0,0,0,0.3);border:4px solid rgba(255,255,255,0.2);"/>'
            )
        else:
            initial = e((self.name or ' ')[0].upper())
            image_html = (
                f'<div style="width:200px;height:200px;border-radius:24px;'
                f'background:rgba(255,255,255,0.1);border:4px solid rgba(255,255,255,0.2);'
                f'font-size:4rem;font-weight:700;color:#fff;'
                f'display:inline-flex;align-items:center;justify-content:center;">'
                f'{initial}</div>'
            )

        # ── Subtitle (rank — subject) ────────────────────────────────
        sub_parts = []
        if self.rank:
            sub_parts.append(e(self.rank))
        if self.subject:
            sub_parts.append(e(self.subject))
        subtitle_html = ''
        if sub_parts:
            subtitle_html = (
                f'<p style="color:rgba(255,255,255,0.8);font-size:1.1rem;margin-bottom:16px;">'
                f'{" &mdash; ".join(sub_parts)}</p>'
            )

        # ── Metadata pills ───────────────────────────────────────────
        pill = ('background:rgba(255,255,255,0.15);color:#fff;'
                'padding:4px 12px;border-radius:20px;font-size:0.82rem;font-weight:500;')
        pills = []
        if self.department:
            pills.append(f'<span style="{pill}">{e(self.department)}</span>')
        if self.position_id:
            pills.append(f'<span style="{pill}">{e(self.position_id.name)}</span>')
        if self.category_id:
            pills.append(f'<span style="{pill}">{e(self.category_id.name)}</span>')
        pills_html = ''
        if pills:
            pills_html = (f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;">'
                          f'{"".join(pills)}</div>')

        # ── Social links + CV ────────────────────────────────────────
        soc = ('background:rgba(255,255,255,0.12);color:#fff;'
               'border:1px solid rgba(255,255,255,0.3);border-radius:8px;'
               'padding:7px 16px;text-decoration:none;font-size:0.87rem;'
               'display:inline-flex;align-items:center;gap:6px;')
        cv_sty = ('background:#f59e0b;color:#1a1a1a;border:none;border-radius:8px;'
                  'padding:7px 16px;text-decoration:none;font-size:0.87rem;font-weight:600;'
                  'display:inline-flex;align-items:center;gap:6px;')
        links = []
        if self.linkedin_url:
            links.append(
                f'<a href="{e(self.linkedin_url)}" target="_blank" rel="noopener noreferrer" '
                f'style="{soc}"><i class="fa fa-linkedin"></i> LinkedIn</a>')
        if self.google_scholar:
            links.append(
                f'<a href="{e(self.google_scholar)}" target="_blank" rel="noopener noreferrer" '
                f'style="{soc}"><i class="fa fa-graduation-cap"></i> Google Scholar</a>')
        if self.research_gate:
            links.append(
                f'<a href="{e(self.research_gate)}" target="_blank" rel="noopener noreferrer" '
                f'style="{soc}"><i class="fa fa-flask"></i> Research Gate</a>')
        if self.email:
            links.append(
                f'<a href="mailto:{e(self.email)}" '
                f'style="{soc}"><i class="fa fa-envelope"></i> Email</a>')
        cv_link = self.cv_download_url
        if cv_link:
            cv_tgt = '' if cv_link.startswith('/') else ' target="_blank" rel="noopener noreferrer"'
            links.append(
                f'<a href="{e(cv_link)}"{cv_tgt} '
                f'style="{cv_sty}"><i class="fa fa-download"></i> Download CV</a>')
        links_html = ''
        if links:
            links_html = f'<div style="display:flex;flex-wrap:wrap;gap:8px;">{"".join(links)}</div>'

        # ── Bio section ──────────────────────────────────────────────
        bio_html = str(self.bio) if self.bio else ''
        if not bio_html and self.subject:
            bio_html = f'<p class="lead"><strong>{e(self.subject)}</strong></p>'
        bio_section = ''
        if bio_html:
            bio_section = f'''
            <section style="background:#fff;padding:48px 0;border-bottom:1px solid #e5e7eb;">
                <div class="container">
                    <div class="row justify-content-center">
                        <div class="col-lg-9">
                            <div class="ypu-bio-content">{bio_html}</div>
                        </div>
                    </div>
                </div>
            </section>'''

        # ── Tabs ─────────────────────────────────────────────────────
        uid = str(self.id)
        tab_defs = [
            (f'personal-{uid}', 'Personal Information', self.personal_info or ''),
            (f'education-{uid}', 'Education',            self.education or ''),
            (f'career-{uid}',    'Career',               self.career or ''),
            (f'admin-{uid}',     'Administration',       self.administration or ''),
            (f'sup-{uid}',       'Supervising',          self.supervising or ''),
            (f'pubs-{uid}',      'Publications',         self.publications or ''),
            (f'courses-{uid}',   'Courses',              self.courses or ''),
        ]
        active_tabs = [
            (tid, tname, str(tcontent))
            for tid, tname, tcontent in tab_defs
            if str(tcontent).strip()
        ]

        tabs_section = ''
        if active_tabs:
            headers_html = ''
            panes_html = ''
            for idx, (tab_id, tab_name, content) in enumerate(active_tabs):
                active_cls = ' active' if idx == 0 else ''
                show_cls = ' show' if idx == 0 else ''
                headers_html += (
                    f'<li class="nav-item" role="presentation">'
                    f'<button class="ypu-tab-btn{active_cls}" '
                    f'data-bs-toggle="tab" data-bs-target="#nav_pane_{tab_id}" '
                    f'type="button" role="tab">{e(tab_name)}</button></li>'
                )
                panes_html += (
                    f'<div class="tab-pane fade{show_cls}{active_cls}" '
                    f'id="nav_pane_{tab_id}" role="tabpanel">'
                    f'<div class="ypu-tab-content">{content}</div>'
                    f'</div>'
                )
            tabs_section = f'''
            <section style="background:#f8faff;padding:48px 0 64px;">
                <div class="container">
                    <ul class="nav ypu-tabs-nav mb-4" role="tablist">{headers_html}</ul>
                    <div class="tab-content">{panes_html}</div>
                </div>
            </section>'''

        return f'''<t t-call="website.layout">
            <div id="wrap">

                <section style="background:linear-gradient(135deg,color-mix(in srgb,var(--bs-primary) 50%,#000000) 0%,var(--bs-primary) 100%);padding:56px 0 48px;">
                    <div class="container">
                        <a href="/teachers" style="color:rgba(255,255,255,0.65);text-decoration:none;font-size:0.85rem;display:inline-flex;align-items:center;gap:6px;margin-bottom:28px;">
                            &#8592; Back to Directory
                        </a>
                        <div class="row align-items-center g-5">
                            <div class="col-lg-7 order-2 order-lg-1">
                                <h1 style="color:#fff;font-weight:700;font-size:2.4rem;margin-bottom:8px;">{name_safe}</h1>
                                {subtitle_html}
                                {pills_html}
                                {links_html}
                            </div>
                            <div class="col-lg-5 order-1 order-lg-2 text-center">
                                {image_html}
                            </div>
                        </div>
                    </div>
                </section>
                {bio_section}
                {tabs_section}

                <div class="oe_structure oe_empty"></div>

            </div>
        </t>'''

    def _create_website_page(self):
        """Create (or regenerate) the editable website.page for this teacher.

        The page is built with the same Odoo snippet classes as the existing
        manually-built profile pages so it looks identical and is fully editable
        in the website builder.  The teacher's Card Link URL is updated to point
        to the new page.
        """
        self.ensure_one()
        if not self.website_slug:
            self.write({
                'website_slug': self._make_unique_slug(self._slugify(self.name))
            })

        page_url = '/' + self.website_slug
        key = f'ypu_teachers.teacher_page_{self.id}'
        arch = self._build_page_arch()

        IrUiView = self.env['ir.ui.view'].sudo()
        WebsitePage = self.env['website.page'].sudo()

        existing_page = self.website_page_id
        if existing_page and existing_page.exists() and existing_page.view_id:
            # Regenerate content; preserve the URL so existing links keep working
            existing_page.view_id.write({'arch_db': arch})
            self.write({'link_url': existing_page.url})
        else:
            # Make sure the URL is not already taken by another page
            taken = WebsitePage.search([('url', '=', page_url)], limit=1)
            if taken:
                page_url = f'/{self.website_slug}-{self.id}'

            view = IrUiView.create({
                'name': f'Teacher: {self.name}',
                'key': key,
                'type': 'qweb',
                'arch_db': arch,
            })
            page = WebsitePage.create({
                'url': page_url,
                'view_id': view.id,
                'is_published': True,
            })
            self.write({
                'website_page_id': page.id,
                'link_url': page_url,
            })

    def action_create_profile_page(self):
        """Button: create or regenerate the dedicated profile page."""
        self.ensure_one()
        self._create_website_page()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Profile page ready at {self.link_url}',
                'type': 'success',
                'sticky': False,
            },
        }

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
