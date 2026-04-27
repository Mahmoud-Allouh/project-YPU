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
        if self.phone:
            parts.append(f'<p class="lead">Mobile phone: {e(self.phone)}</p>')
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
        """Return the arch XML string for this teacher's dedicated website.page view.

        The structure mirrors the existing manually-built profile pages:
        • Section 1 – o_cc5 dark band with teacher name (s_text_block)
        • Section 2 – o_cc2 framed intro with photo + bio (s_framed_intro)
        • Section 3 – o_cc2 tabbed content (s_tabs)
        • Trailing oe_structure for extra snippets
        """
        e = _html_lib.escape
        name_safe = e(self.name or '')

        # ── Photo ────────────────────────────────────────────
        if self.image_1920:
            image_html = (
                f'<img src="/web/image/ypu.teacher/{self.id}/image_1920" '
                f'alt="{name_safe}" class="img img-fluid o_we_custom_image" '
                f'style="width: 100% !important;" loading="lazy"/>'
            )
        else:
            initial = e((self.name or ' ')[0].upper())
            image_html = (
                f'<div style="width:200px;height:200px;border-radius:50%;'
                f'background:#e2e8f0;font-size:4rem;font-weight:700;color:#2563eb;'
                f'display:flex;align-items:center;justify-content:center;margin:0 auto;">'
                f'{initial}</div>'
            )

        # ── Bio ──────────────────────────────────────────────
        bio_html = str(self.bio) if self.bio else ''
        if not bio_html and self.subject:
            bio_html = f'<p class="lead"><strong>{e(self.subject)}</strong></p>'

        # ── Tabs ─────────────────────────────────────────────
        uid = str(self.id)
        tab_defs = [
            (f'personal-{uid}', 'Personal Information', self.personal_info or ''),
            (f'contact-{uid}',  'Contact Information',  self._contact_html()),
            (f'education-{uid}', 'Education',           self.education or ''),
            (f'career-{uid}',   'Career',               self.career or ''),
            (f'admin-{uid}',    'Administration',       self.administration or ''),
            (f'sup-{uid}',      'Supervising',          self.supervising or ''),
            (f'pubs-{uid}',     'Publications',         self.publications or ''),
            (f'courses-{uid}',  'Courses',              self.courses or ''),
        ]
        active_tabs = [
            (tid, tname, str(tcontent))
            for tid, tname, tcontent in tab_defs
            if str(tcontent).strip()
        ]

        headers_html = ''
        panes_html = ''
        for idx, (tab_id, tab_name, content) in enumerate(active_tabs):
            active_cls = ' active' if idx == 0 else ''
            show_cls = ' show' if idx == 0 else ''
            selected = 'true' if idx == 0 else 'false'
            headers_html += (
                f'\n                        <li class="nav-item" role="presentation">'
                f'\n                            <a class="nav-link text-break{active_cls}"'
                f' id="nav_tab_{tab_id}" data-bs-toggle="tab"'
                f' href="#nav_pane_{tab_id}" role="tab"'
                f' aria-controls="nav_pane_{tab_id}" aria-selected="{selected}">'
                f'{e(tab_name)}</a>'
                f'\n                        </li>'
            )
            panes_html += (
                f'\n                    <div class="tab-pane fade{show_cls}{active_cls}"'
                f' id="nav_pane_{tab_id}" role="tabpanel"'
                f' aria-labelledby="nav_tab_{tab_id}">'
                f'\n                        <div class="oe_structure oe_empty">'
                f'\n                            <section class="s_text_block" data-snippet="s_text_block">'
                f'\n                                <div class="container s_allow_columns">'
                f'\n                                    {content}'
                f'\n                                </div>'
                f'\n                            </section>'
                f'\n                        </div>'
                f'\n                    </div>'
            )

        tabs_section = ''
        if active_tabs:
            tabs_section = f'''
            <section class="s_tabs_common s_tabs o_colored_level pb144 o_cc o_cc2 pt16 o_half_screen_height"
                     data-vcss="003" data-vxml="002" data-snippet="s_tabs" data-name="Tabs">
                <div class="container">
                    <div class="s_tabs_main o_direction_horizontal">
                        <div class="s_tabs_nav mb-3 overflow-y-hidden overflow-x-auto"
                             data-name="Tab Header" role="navigation">
                            <ul class="nav nav-underline flex-nowrap nav-justified" role="tablist">
                                {headers_html}
                            </ul>
                        </div>
                        <div class="s_tabs_content tab-content">
                            {panes_html}
                        </div>
                    </div>
                </div>
            </section>'''

        return f'''<t t-call="website.layout">
            <div id="wrap" class="oe_structure oe_empty">

                <section class="s_text_block pt40 o_colored_level o_cc o_cc5 pb32"
                         data-snippet="s_text_block">
                    <div class="s_allow_columns container">
                        <div class="row o_grid_mode" data-row-count="2">
                            <div class="o_grid_item g-col-lg-12 o_colored_level g-height-2 col-lg-12"
                                 style="grid-area: 1 / 1 / 3 / 13; z-index: 1;">
                                <h1 style="text-align: center;">{name_safe}</h1>
                            </div>
                        </div>
                    </div>
                </section>

                <section class="s_framed_intro o_colored_level o_cc o_cc2 pb32 pt64"
                         data-snippet="s_framed_intro" data-name="Framed Intro">
                    <div class="container">
                        <div class="row o_grid_mode" data-row-count="8">
                            <div class="o_grid_item o_grid_item_image o_cc o_colored_level g-col-lg-5 g-height-8 col-lg-5 o_cc3 rounded"
                                 style="grid-area: 1 / 8 / 9 / 13; z-index: 3;
                                        --grid-item-padding-y: 32px; --grid-item-padding-x: 32px;
                                        --box-border-bottom-left-radius: 35px;
                                        --box-border-bottom-right-radius: 35px;
                                        --box-border-top-right-radius: 35px;
                                        --box-border-top-left-radius: 35px;">
                                {image_html}
                            </div>
                            <div class="o_grid_item g-col-lg-6 align-content-end o_colored_level g-height-5 col-lg-6"
                                 style="z-index: 2; grid-area: 2 / 1 / 7 / 7;">
                                {bio_html}
                            </div>
                        </div>
                    </div>
                </section>
                {tabs_section}

                <div class="oe_structure oe_empty"/>

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
