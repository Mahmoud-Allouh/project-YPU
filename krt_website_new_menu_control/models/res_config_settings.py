from odoo import fields, models

KEYS = [
    "wnm_hide_page",
    "wnm_hide_blog",
    "wnm_hide_product",
    "wnm_hide_event",
    "wnm_hide_job",
    "wnm_hide_forum",
    "wnm_hide_appointment",
    "wnm_hide_course",
]

class WebsiteNewMenuSettings(models.TransientModel):
    _inherit = "res.config.settings"

    wnm_hide_page = fields.Boolean("Hide: Page")
    wnm_hide_blog = fields.Boolean("Hide: Blog Post")
    wnm_hide_product = fields.Boolean("Hide: Product")
    wnm_hide_event = fields.Boolean("Hide: Event")
    wnm_hide_job = fields.Boolean("Hide: Job Position")
    wnm_hide_forum = fields.Boolean("Hide: Forum")
    wnm_hide_appointment = fields.Boolean("Hide: Appointment / Live Chat")
    wnm_hide_course = fields.Boolean("Hide: Course/LMS")

    def get_values(self):
        res = super().get_values()
        ICP = self.env["ir.config_parameter"].sudo()
        for k in KEYS:
            res[k] = ICP.get_param(f"website_new_menu_control.{k}", "0") == "1"
        return res

    def set_values(self):
        super().set_values()
        ICP = self.env["ir.config_parameter"].sudo()
        for k in KEYS:
            ICP.set_param(f"website_new_menu_control.{k}", "1" if getattr(self, k) else "0")
