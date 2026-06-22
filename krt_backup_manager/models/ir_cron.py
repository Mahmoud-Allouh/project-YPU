from odoo import models


class IrCron(models.Model):
    _inherit = "ir.cron"

    def method_direct_trigger(self):
        for rec in self:
            rec = rec.with_context(cron_id=rec.id)
            super(IrCron, rec).method_direct_trigger()
        return True
