import html as _html_lib
import re
import unicodedata

from odoo import api, fields, models


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
    pdf_file = fields.Binary(string='Course PDF', attachment=True)
    pdf_filename = fields.Char(string='PDF Filename')

    # ── Website page ─────────────────────────────────────────────
    website_slug = fields.Char(
        string='URL Slug',
        copy=False,
        index=True,
        help='Used in the course page address. Auto-generated from the course code.',
    )
    website_page_id = fields.Many2one(
        'website.page',
        string='Website Page',
        copy=False,
        ondelete='set null',
        index=True,
        help='The editable website page generated for this course.',
    )
    page_url = fields.Char(
        string='Page Address',
        compute='_compute_page_url',
        help='Public address of this course page on the website.',
    )

    @api.depends('website_page_id', 'website_page_id.url', 'website_slug')
    def _compute_page_url(self):
        for rec in self:
            if rec.website_page_id and rec.website_page_id.url:
                rec.page_url = rec.website_page_id.url
            elif rec.website_slug:
                rec.page_url = f'/courses/{rec.website_slug}'
            else:
                rec.page_url = False

    # ── Slug helpers ─────────────────────────────────────────────

    @staticmethod
    def _slugify(text):
        if not text:
            return ''
        s = unicodedata.normalize('NFKD', text)
        s = s.encode('ascii', 'ignore').decode('ascii')
        s = s.lower()
        s = re.sub(r'[^\w\s-]', '', s)
        s = re.sub(r'[\s_]+', '-', s.strip())
        return s.strip('-')

    def _make_unique_slug(self, base_slug):
        if not base_slug:
            base_slug = f'course-{self.id}'
        slug = base_slug
        counter = 2
        while self.search_count([('website_slug', '=', slug), ('id', '!=', self.id)]):
            slug = f'{base_slug}-{counter}'
            counter += 1
        return slug

    # ── Page builder ─────────────────────────────────────────────

    def _build_page_arch(self):
        """Return QWeb arch for this course's editable website.page."""
        e = _html_lib.escape
        code_safe = e(self.code or '')
        name_ar_safe = e(self.name_ar or '')
        name_en_safe = e(self.name_en or '')
        plan_name_safe = e(self.plan_id.name or '') if self.plan_id else ''

        # ── Hero pills (code + plan) ──────────────────────────────
        pill = ('background:rgba(255,255,255,0.16);color:#fff;'
                'padding:4px 14px;border-radius:20px;font-size:0.85rem;font-weight:600;')
        pill_soft = ('background:rgba(255,255,255,0.10);color:rgba(255,255,255,0.78);'
                     'padding:4px 14px;border-radius:20px;font-size:0.85rem;')
        pills = []
        if code_safe:
            pills.append(f'<span style="{pill}">{code_safe}</span>')
        if plan_name_safe:
            pills.append(f'<span style="{pill_soft}">{plan_name_safe}</span>')
        pills_html = (
            f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px;">'
            f'{"".join(pills)}</div>'
        ) if pills else ''

        # ── Hero titles ───────────────────────────────────────────
        title_html = ''
        if name_ar_safe:
            title_html += (
                f'<h1 style="color:#fff;font-weight:700;font-size:2.2rem;margin-bottom:8px;">'
                f'{name_ar_safe}</h1>'
            )
        if name_en_safe:
            title_html += (
                f'<p style="color:rgba(255,255,255,0.82);font-size:1.1rem;margin-bottom:0;">'
                f'{name_en_safe}</p>'
            )

        hero = (
            f'<section style="background:linear-gradient(135deg,'
            f'color-mix(in srgb,var(--bs-primary) 50%,#000000) 0%,'
            f'var(--bs-primary) 100%);padding:56px 0 48px;">'
            f'<div class="container">{pills_html}{title_html}</div></section>'
        )

        # ── Hours cards ───────────────────────────────────────────
        card = ('border:1px solid #e5e7eb;border-radius:12px;padding:20px;'
                'text-align:center;background:#fff;')
        cards = []

        def _card(value, label, color):
            return (
                f'<div class="col-md-4 col-6">'
                f'<div style="{card}">'
                f'<div style="font-size:1.8rem;font-weight:700;color:{color};">{value:g}</div>'
                f'<div style="color:#6b7280;font-size:0.85rem;margin-top:4px;">{label}</div>'
                f'</div></div>'
            )

        if self.theory_hours:
            cards.append(_card(self.theory_hours, 'Theory Hours', 'var(--bs-primary)'))
        if self.practical_hours:
            cards.append(_card(self.practical_hours, 'Practical Hours', 'var(--bs-primary)'))
        if self.credit_hours:
            cards.append(_card(self.credit_hours, 'Credit Hours (CH)', '#16a34a'))
        cards_html = f'<div class="row g-3 mb-4">{"".join(cards)}</div>' if cards else ''

        # ── Prerequisite ──────────────────────────────────────────
        prereq_html = ''
        if self.prerequisite:
            prereq_html = (
                f'<p style="margin-bottom:16px;"><strong>Prerequisite:</strong> '
                f'{e(self.prerequisite)}</p>'
            )

        # ── Description ───────────────────────────────────────────
        desc_html = ''
        if self.description:
            body = e(self.description).replace('\n', '<br/>')
            desc_html = (
                f'<div style="line-height:1.75;color:#374151;margin-top:8px;">{body}</div>'
            )

        # ── PDF download ──────────────────────────────────────────
        pdf_html = ''
        if self.pdf_file:
            pdf_url = (
                f'/web/content/ypu.study.plan.course/{self.id}/pdf_file?download=true'
            )
            pdf_html = (
                f'<p style="margin-top:24px;">'
                f'<a href="{pdf_url}" '
                f'style="display:inline-flex;align-items:center;gap:8px;'
                f'padding:9px 20px;border:1px solid #d1d5db;border-radius:8px;'
                f'text-decoration:none;color:#374151;font-size:0.9rem;">'
                f'<i class="fa fa-file-pdf-o"></i> Download PDF</a></p>'
            )

        body_content = cards_html + prereq_html + desc_html + pdf_html
        body = (
            f'<section style="background:#f8faff;padding:48px 0;">'
            f'<div class="container">{body_content}</div></section>'
        ) if body_content.strip() else ''

        return (
            f'<t t-call="website.layout">'
            f'<div id="wrap">'
            f'{hero}{body}'
            f'<div class="oe_structure oe_empty"></div>'
            f'</div>'
            f'</t>'
        )

    def _create_course_page(self):
        """Create (or regenerate) the editable website.page for this course."""
        self.ensure_one()
        if not self.website_slug:
            base = self._slugify(self.code or '') or f'course-{self.id}'
            self.write({'website_slug': self._make_unique_slug(base)})

        page_url = f'/courses/{self.website_slug}'
        key = f'ypu_study_plans.course_page_{self.id}'
        arch = self._build_page_arch()

        IrUiView = self.env['ir.ui.view'].sudo()
        WebsitePage = self.env['website.page'].sudo()

        existing = self.website_page_id
        if existing and existing.exists() and existing.view_id:
            # Regenerate body; keep the URL stable so existing links still work
            existing.view_id.write({'arch_db': arch})
        else:
            taken = WebsitePage.search([('url', '=', page_url)], limit=1)
            if taken:
                page_url = f'/courses/{self.website_slug}-{self.id}'
            view = IrUiView.create({
                'name': f'Course: {self.code or self.name_en or self.name_ar or self.id}',
                'key': key,
                'type': 'qweb',
                'arch_db': arch,
            })
            page = WebsitePage.create({
                'url': page_url,
                'view_id': view.id,
                'is_published': True,
            })
            self.write({'website_page_id': page.id})

    def action_create_course_page(self):
        """Button: create or regenerate this course's editable website page."""
        self.ensure_one()
        self._create_course_page()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Course page ready',
                'message': f'The page is live at {self.page_url}',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def action_open_course_page(self):
        """Button: open the live course page on the website."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.page_url or '/',
            'target': 'new',
        }
