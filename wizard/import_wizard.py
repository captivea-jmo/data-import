from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import tempfile

class ImportWizard(models.TransientModel):
    _name = 'import.wizard'
    _description = 'Import Wizard for XLSX'

    file = fields.Binary('File', required=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True,
                               help="Select the model into which you want to import the data")
    username = fields.Char(string="Username", default=lambda self: self.env.user.login, readonly=True)
    password = fields.Char(string="Password", required=True, help="Enter your Odoo password", password=True)

    def action_import(self):
        if not self.file:
            raise UserError("Please upload a file before importing.")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            tmp_file.write(base64.b64decode(self.file))
            tmp_file_path = tmp_file.name

        # Call the import function with username and password
        success, message = self.env['import.data'].import_from_xlsx(
            tmp_file_path, self.model_id.model, self.username, self.password
        )

        if not success:
            raise UserError(f"Import failed: {message}")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': True,
            }
        }
