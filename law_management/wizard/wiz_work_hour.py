# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MatterWorkingHour(models.TransientModel):
    _name = 'matter.work.hour'
    _description = 'Matter Working Hour'

    work_hour = fields.Float('Working Hour')

    @api.constrains('work_hour')
    def check_work_hour(self):
        """
        This method is used to validate the working hour.
        -------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        for rec in self:
            if rec.work_hour <= 0.0:
                raise ValidationError(_('Invalid working hours!'))

    def wiz_work_hour(self):
        """
        This method is used to create invoice and invoice lines.
        --------------------------------------------------------
        @param self: object pointer
        """
        matt_id = self._context.get('active_id')
        curr_dt = datetime.now()
        cr_dt = curr_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        matter_obj = self.env['matter.matter'].browse(matt_id)
        inv_obj = self.env['account.move']
        inv_line_obj = self.env['account.move.line']
        invoice_line_vals = []
        if matter_obj:
            journal_id = inv_obj.with_context(
                default_move_type='out_invoice')._get_default_journal()
            inv_line_vals = {
                'name': matter_obj.name,
                'price_unit': matter_obj.assign_id.fees_hour,
                'account_id': journal_id and
                journal_id.default_account_id and
                journal_id.default_account_id.id
                or False,
                'quantity': self.work_hour,
            }
            invoice_line_vals.append((0, 0, inv_line_vals))
            inv_vals = {
                'partner_id': matter_obj.mat_client and
                matter_obj.mat_client.id or False,
                'invoice_date': cr_dt,
                'user_id': matter_obj.assign_id
                and matter_obj.assign_id.user_id and
                matter_obj.assign_id.user_id.id or False,
                'matter_id': matter_obj.id or False,
                'pay_type': 'pay_per_hour',
                'move_type': 'out_invoice',
                'state': 'draft',
                'journal_id': journal_id and journal_id.id or False,
                'invoice_line_ids': invoice_line_vals,
                'auto_post': False,
                'payment_state': 'not_paid',
            }
            inv_id = self.env['account.move'].create(inv_vals)
            inv_id._onchange_partner_id()
            matter_obj.invoice_id = inv_id.id
            matter_trial = self.env['matter.trial'].search(
                [('matter_id', '=', matter_obj.id)])
            matter_trial.is_invoice = True
