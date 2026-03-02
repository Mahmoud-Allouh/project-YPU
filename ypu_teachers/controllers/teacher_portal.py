import math
from urllib.parse import urlencode

from odoo.http import Controller, request, route

TEACHERS_PER_PAGE = 12


class YpuTeacherPortal(Controller):

    @route('/teachers', type='http', auth='public', website=True, sitemap=True)
    def teacher_list(self, search='', category_id='', available='', page='1', **kw):
        Teacher = request.env['ypu.teacher'].sudo()
        Category = request.env['ypu.teacher.category'].sudo()

        # ── Parse filters ────────────────────────────────────
        cat_id = int(category_id) if category_id and str(category_id).isdigit() else False
        avail_flag = self._parse_available(available)

        domain = Teacher.website_search_domain(
            search=search.strip(),
            category_id=cat_id,
            available=avail_flag,
        )

        # ── Pagination ───────────────────────────────────────
        total = Teacher.search_count(domain)
        current_page = max(int(page), 1) if str(page).isdigit() else 1
        total_pages = max(math.ceil(total / TEACHERS_PER_PAGE), 1)
        current_page = min(current_page, total_pages)
        offset = (current_page - 1) * TEACHERS_PER_PAGE

        teachers = Teacher.search(
            domain,
            limit=TEACHERS_PER_PAGE,
            offset=offset,
            order='sequence, is_dean desc, name',
        )

        categories = Category.search([('active', '=', True)], order='sequence, name')

        # ── Build pager data ─────────────────────────────────
        url_args = {}
        if search:
            url_args['search'] = search
        if cat_id:
            url_args['category_id'] = cat_id
        if avail_flag is not None:
            url_args['available'] = '1' if avail_flag else '0'

        pager = self._build_pager('/teachers', total, current_page, TEACHERS_PER_PAGE, url_args)

        return request.render('ypu_teachers.website_teachers', {
            'teachers': teachers,
            'categories': categories,
            'search': search,
            'selected_category': cat_id,
            'selected_available': avail_flag,
            'pager': pager,
            'total': total,
        })

    # ── Private helpers ──────────────────────────────────────

    @staticmethod
    def _parse_available(value):
        """Convert the *available* query-string value to a tri-state bool."""
        if not value:
            return None
        val = str(value).lower()
        if val in ('1', 'true', 'yes'):
            return True
        if val in ('0', 'false', 'no'):
            return False
        return None

    @staticmethod
    def _build_pager(base_url, total, page, step, url_args):
        """Return a dict consumed by the website_teachers pager snippet."""
        total_pages = max(math.ceil(total / step), 1)
        page = max(1, min(page, total_pages))

        def _url(p):
            args = dict(url_args, page=p)
            return f'{base_url}?{urlencode(args)}'

        return {
            'total_pages': total_pages,
            'current': page,
            'pages': [
                {'num': p, 'url': _url(p), 'active': p == page}
                for p in range(1, total_pages + 1)
            ],
            'prev_url': _url(page - 1) if page > 1 else False,
            'next_url': _url(page + 1) if page < total_pages else False,
        }
