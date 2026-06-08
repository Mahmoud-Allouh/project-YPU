from odoo import fields, models


class WebsiteEditRestriction(models.Model):
    _name = "ypu.website.edit.restriction"
    _description = "Website Edit Restriction"
    _rec_name = "user_id"
    _order = "user_id"

    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        ondelete="cascade",
        domain=[("share", "=", False)],
    )
    restriction_enabled = fields.Boolean(
        string="Limit Website Editing",
        default=True,
        help="When enabled, this user can edit only the selected pages and blogs.",
    )
    allowed_page_ids = fields.Many2many(
        "website.page",
        "ypu_web_edit_restrict_page_rel",
        "restriction_id",
        "page_id",
        string="Allowed Website Pages",
    )
    allowed_blog_ids = fields.Many2many(
        "blog.blog",
        "ypu_web_edit_restrict_blog_rel",
        "restriction_id",
        "blog_id",
        string="Allowed Blogs",
    )

    _user_unique = models.Constraint(
        "unique (user_id)",
        "Each user can only have one website edit restriction record.",
    )
