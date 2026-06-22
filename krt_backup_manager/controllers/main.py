from odoo import http
from odoo.http import request


class BackupCenterDownloadController(http.Controller):
    @http.route("/web/binary/download-backup", type="http", auth="user")
    def download_backup_center_file(
        self, model, id, file_name_field, file_path_field, file_format, **kw
    ):
        record = request.env[model].sudo().browse(int(id))
        fichier = b""
        with open(record[file_path_field], "rb") as f:
            fichier = f.read()
        filename = record[file_name_field]
        headers = [
            ("Content-Type", f"application/{file_format}"),
            ("Content-Disposition", f"attachment; filename={filename}"),
        ]
        return request.make_response(fichier, headers=headers)
