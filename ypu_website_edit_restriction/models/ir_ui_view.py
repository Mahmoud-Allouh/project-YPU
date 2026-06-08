from odoo import models


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    def _linked_website_pages(self):
        return self.env["website.page"].sudo().search([("view_id", "in", self.ids)])

    def write(self, vals):
        linked_pages = self._linked_website_pages()
        if linked_pages:
            self.env.user._check_allowed_website_pages(linked_pages)
        return super().write(vals)

    def unlink(self):
        linked_pages = self._linked_website_pages()
        if linked_pages:
            self.env.user._check_allowed_website_pages(linked_pages)
        return super().unlink()
