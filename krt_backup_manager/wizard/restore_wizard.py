from odoo.service import db
from odoo.http import dispatch_rpc
from odoo import SUPERUSER_ID, fields, models, tools, api, sql_db, _


class DataBaseRestoreInstance(models.TransientModel):
    _name = "db.restore.instance.wizard"
    _description = _("Database Restore Wizard")

    restore_db_name = fields.Char(
        string=_("Database Name"),
        help=_("Name of the new database"),
        required=True,
    )
    restore_master_pwd = fields.Char(
        string=_("Master Password"),
        help=_("Master password for restoring the database"),
        required=True,
    )
    is_copy = fields.Boolean(string=_("This database is a copy"))
    reset_admin_account_access = fields.Boolean(
        string=_("Reset Administrator Access")
    )
    admin_username = fields.Char(string=_("Administrator Username"))
    admin_password = fields.Char(string=_("Administrator Password"))
    backup_id = fields.Many2one(
        "db.backup.instance", string=_("Backup to Restore"), required=True
    )

    def restorer(self):
        insecure = tools.config.verify_admin_password("admin")
        if insecure and self.restore_master_pwd:
            dispatch_rpc(
                "db", "change_admin_password", ["admin", self.restore_master_pwd]
            )
        db.check_super(self.restore_master_pwd)
        res = self.backup_id.restore_backup(self.restore_db_name, self.is_copy)
        if self.reset_admin_account_access:
            self.reset_admin_access()
        return res

    def reset_admin_access(self):
        SUPERUSER_ID_ADMIN = SUPERUSER_ID + 1
        current_cursor = sql_db.db_connect(self.restore_db_name).cursor()
        env = api.Environment(current_cursor, SUPERUSER_ID, {})
        admin_user = env["res.users"].search([("id", "=", SUPERUSER_ID_ADMIN)])
        admin_user.write(
            {"password": self.admin_password, "login": self.admin_username}
        )
        current_cursor.commit()
        current_cursor.close()
