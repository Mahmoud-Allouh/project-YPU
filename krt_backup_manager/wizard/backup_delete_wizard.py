from odoo import fields, models, _

class DataBaseDeleteInstance(models.TransientModel):
    _name = "db.delete.instance"
    _description = _("Database Deletion Assistant")

    delete_attach_file = fields.Boolean(string=_("Delete Associated File"))
    backup_id = fields.Many2one("db.backup.instance", string=_("Backup to Delete"), required=True)
    file_exist = fields.Boolean(string=_("File Present"))

    def confirm_deletion(self):
        if self.file_exist and self.delete_attach_file:
            self.backup_id.delete_db_backup_file()
        self.backup_id.sudo().unlink()
        return True
