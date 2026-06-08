from odoo import _, api, models
from odoo.exceptions import AccessError


class BlogPost(models.Model):
    _inherit = "blog.post"

    @api.model_create_multi
    def create(self, vals_list):
        user = self.env.user
        records = super().create(vals_list)
        if user._is_website_restriction_active():
            user._check_allowed_blogs(records.mapped("blog_id"))
        return records

    def write(self, vals):
        user = self.env.user
        user._check_allowed_blogs(self.mapped("blog_id"))
        if vals.get("blog_id"):
            user._check_allowed_blogs(self.env["blog.blog"].browse(vals["blog_id"]))
        return super().write(vals)

    def unlink(self):
        self.env.user._check_allowed_blogs(self.mapped("blog_id"))
        return super().unlink()
