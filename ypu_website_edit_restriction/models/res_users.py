from odoo import _, fields, models
from odoo.exceptions import AccessError


class ResUsers(models.Model):
    _inherit = "res.users"

    website_restriction_enabled = fields.Boolean(
        string="Limit Website Editing",
        help="When enabled, this user can edit only the pages and blogs selected below.",
    )
    website_allowed_page_ids = fields.Many2many(
        "website.page",
        "res_users_website_page_rel",
        "user_id",
        "page_id",
        string="Allowed Website Pages",
        help="Pages this user is allowed to edit.",
    )
    website_allowed_blog_ids = fields.Many2many(
        "blog.blog",
        "res_users_blog_rel",
        "user_id",
        "blog_id",
        string="Allowed Blogs",
        help="Blogs this user is allowed to manage.",
    )

    def _get_website_restriction_data(self):
        self.ensure_one()
        page_model = self.env["website.page"]
        blog_model = self.env["blog.blog"]

        if self.has_group("base.group_system"):
            return False, page_model, blog_model

        restriction = self.env["ypu.website.edit.restriction"].sudo().search(
            [("user_id", "=", self.id)], limit=1
        )
        if restriction:
            return (
                bool(restriction.restriction_enabled),
                restriction.allowed_page_ids.sudo(),
                restriction.allowed_blog_ids.sudo(),
            )

        # Backward compatible fallback for legacy values saved before this refactor.
        return (
            bool(self.website_restriction_enabled),
            self.website_allowed_page_ids.sudo(),
            self.website_allowed_blog_ids.sudo(),
        )

    def _is_website_restriction_active(self):
        self.ensure_one()
        enabled, _, _ = self._get_website_restriction_data()
        return enabled

    def _check_allowed_website_pages(self, pages):
        self.ensure_one()
        enabled, allowed_pages, _ = self._get_website_restriction_data()
        if not enabled or not pages:
            return

        pages = pages.sudo()
        forbidden_pages = pages - allowed_pages
        if not forbidden_pages:
            return

        labels = forbidden_pages.sudo().mapped(lambda page: page.name or page.url)
        raise AccessError(
            _(
                "You are not allowed to edit these website pages:\n%s"
            )
            % "\n".join(labels)
        )

    def _check_allowed_blogs(self, blogs):
        self.ensure_one()
        enabled, _, allowed_blogs = self._get_website_restriction_data()
        if not enabled or not blogs:
            return

        blogs = blogs.sudo()
        forbidden_blogs = blogs - allowed_blogs
        if not forbidden_blogs:
            return

        labels = forbidden_blogs.sudo().mapped("name")
        raise AccessError(
            _(
                "You are not allowed to edit content in these blogs:\n%s"
            )
            % "\n".join(labels)
        )
