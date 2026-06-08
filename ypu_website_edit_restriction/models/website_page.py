from odoo import _, api, models
from odoo.exceptions import AccessError


class WebsitePage(models.Model):
    _inherit = "website.page"

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user._is_website_restriction_active():
            raise AccessError(
                _("You are not allowed to create new website pages.")
            )
        return super().create(vals_list)

    def write(self, vals):
        self.env.user._check_allowed_website_pages(self)
        return super().write(vals)

    def unlink(self):
        self.env.user._check_allowed_website_pages(self)
        return super().unlink()
