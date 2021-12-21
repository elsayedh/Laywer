# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class TrialInvoice(models.Model):
    _inherit = 'account.move'

    matter_id = fields.Many2one('matter.matter', 'Matter Name')
    trial_id = fields.Many2one('matter.trial', 'Trial')
    pay_type = fields.Selection(related='matter_id.pay_type',
                                string='Payment Type')
    payment_mode = fields.Selection([('cash', 'Cash'), ('check', 'Check')],
                                    string='Payment Mode')


class InvoiceLines(models.Model):
    _inherit = 'account.move.line'

    pay_type = fields.Selection(related='move_id.pay_type',
                                string='Payment Type')
