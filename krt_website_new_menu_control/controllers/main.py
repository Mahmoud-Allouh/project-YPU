from odoo import http

KEYS = [
    "wnm_hide_page", "wnm_hide_blog", "wnm_hide_product", "wnm_hide_event",
    "wnm_hide_job", "wnm_hide_forum", "wnm_hide_appointment", "wnm_hide_course",
]

class WebsiteNewMenuController(http.Controller):
    @http.route("/website_new_menu_control/config", type="http", auth="user", methods=["GET"], csrf=False)
    def get_config(self):
        ICP = http.request.env["ir.config_parameter"].sudo()
        cfg = {k: ICP.get_param(f"website_new_menu_control.{k}", "0") == "1" for k in KEYS}
        return http.request.make_json_response(cfg)
