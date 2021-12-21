# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MatterReopen(models.TransientModel):
    _name = 'matter.reopen.wizard'
    _description = 'Matter Reopen'

    reopen_id = fields.Many2one('matter.matter')
    reopen_date = fields.Date('Date')
    reason = fields.Text('Reason')

    @api.constrains('reopen_date')
    def check_reopen_date(self):
        """
        This method is used to validate Reopen Date.
        --------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        matt_id = self._context.get('active_id')
        matter_obj = self.env['matter.matter'].browse(matt_id)
        current_date = fields.Date.today()
        for rec in self:
            if rec.reopen_date > current_date:
                raise ValidationError(_(
                    'Reopen Date should be'
                    ' less than or equal to Current Date!'))
            if rec.reopen_date <= matter_obj.date_close:
                raise ValidationError(_('Reopen date should be greater than'
                                        ' Close Date!'))

    def wiz_reason_action(self):
        """
        This method will create an action to \
        give reason for reopening the matter.
        --------------------------------------
        @param self : object pointer
        """
        mat_id = self._context.get('active_id')
        ac_reason = self.reason
        re_date = self.reopen_date
        matter_rec = self.env['matter.matter'].browse(mat_id)
        if matter_rec:
            if matter_rec.state == 'win':
                cases_won = matter_rec.sudo().assign_id.case_won
                cases_won -= 1
                matter_rec.sudo().assign_id.case_won = cases_won
            if matter_rec.state == 'lost':
                cases_lost = matter_rec.sudo().assign_id.case_lost
                cases_lost -= 1
                matter_rec.sudo().assign_id.case_lost = cases_lost
            if matter_rec.state == 'settlement':
                cases_settle = matter_rec.sudo().assign_id.case_settle
                cases_settle -= 1
                matter_rec.sudo().assign_id.case_settle = cases_settle
            case_assign = matter_rec.sudo().assign_id.case_assign
            case_assign += 1
            matter_rec.sudo().assign_id.case_assign = case_assign
            matter_rec.state = 're_open'
            matter_rec.is_reopen = True,
            matter_rec.reopen_date = re_date
            act_obj = self.env['matter.history']
            act_vals = {
                'name': dict(matter_rec._fields.get('state').selection).
                get(matter_rec.state),
                'hist_date': re_date,
                'reason': ac_reason,
                'history_id': matter_rec.id,
            }
            act_obj.create(act_vals)
