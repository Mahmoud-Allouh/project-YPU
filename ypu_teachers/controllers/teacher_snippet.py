import math

from odoo.http import Controller, request, route


class YpuTeacherSnippet(Controller):
    """JSON-RPC controller consumed by the dynamic teacher-cards snippet."""

    @route('/ypu_teachers/snippet/teachers', type='jsonrpc', auth='public', website=True)
    def snippet_teachers(self, category_id=False, limit=4, page=1, **kw):
        Teacher = request.env['ypu.teacher'].sudo()

        domain = [
            ('website_published', '=', True),
            ('is_public', '=', True),
        ]
        if category_id:
            domain.append(('category_id', '=', int(category_id)))

        total = Teacher.search_count(domain)
        limit = int(limit)

        if limit <= 0:
            # Carousel mode: fetch all matching teachers
            teachers = Teacher.search(domain, order='sequence, is_dean desc, name')
            page = 1
            total_pages = 1
        else:
            page = max(int(page), 1)
            total_pages = max(math.ceil(total / limit), 1)
            page = min(page, total_pages)
            offset = (page - 1) * limit
            teachers = Teacher.search(
                domain, limit=limit, offset=offset,
                order='sequence, is_dean desc, name',
            )

        return {
            'teachers': [
                {
                    'id': t.id,
                    'name': t.name,
                    'department': t.department or '',
                    'subject': t.subject or '',
                    'rank': t.rank or '',
                    'email': t.email or '',
                    'phone': t.phone or '',
                    'linkedin_url': t.linkedin_url or '',
                    'research_gate': t.research_gate or '',
                    'available': t.available,
                    'is_dean': t.is_dean,
                    'category': t.category_id.name if t.category_id else '',
                    'position': t.position_id.name if t.position_id else '',
                    'has_image': bool(t.image_1920),
                    'image_url': f'/web/image/ypu.teacher/{t.id}/image_1920',
                    'show_link_button': t.show_link_button,
                    'link_url': t.link_url or '',
                }
                for t in teachers
            ],
            'total': total,
            'page': page,
            'total_pages': total_pages,
        }

    @route('/ypu_teachers/snippet/categories', type='jsonrpc', auth='public', website=True)
    def snippet_categories(self, **kw):
        """Return active categories for the snippet configurator."""
        Category = request.env['ypu.teacher.category'].sudo()
        cats = Category.search([('active', '=', True)], order='sequence, name')
        return [{'id': c.id, 'name': c.name} for c in cats]
