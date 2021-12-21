# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MatterClose(models.TransientModel):
    _name = 'matter.close.wizard'
    _description = 'Matter Close'

    date = fields.Date('Result Date')
    descript = fields.Text('Result Description')
    act_type = fields.Selection([('win', 'Won'),
                                 ('lost', 'Lost'),
                                 ('settlement', 'Settlement')],
                                string='Result Type')

    @api.constrains('date')
    def check_date_close(self):
        """
        This method is used to validate the Result Date.
        ------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        matt_id = self._context.get('active_id')
        matter_obj = self.env['matter.matter'].browse(matt_id)
        current_date = fields.Date.today()
        for rec in self:
            if rec.date and rec.date > current_date:
                raise ValidationError(_(
                    'Result Date should be'
                    ' less than or equal to Current Date!'))
            if rec.date:
                if matter_obj.trial_date and rec.date\
                        and rec.date <= matter_obj.trial_date:
                    raise ValidationError(_('Close date of matter should be'
                                            ' greater than Trial Date!'))
                if matter_obj.reopen_date and rec.date\
                        and rec.date <= matter_obj.reopen_date:
                    raise ValidationError(_('Close date of matter should be'
                                            ' greater than Re-Open Date'))
                if matter_obj.date_open and rec.date\
                        and rec.date <= matter_obj.date_open:
                    raise ValidationError(_('Result Date should be greater'
                                            ' than Open Date! '))

    def wiz_close_action(self):
        """
        This method will create an action to no action against employee \
        when clicked on Take Action Button and will create the history of the \
        closed matter.
        ----------------------------------------------------------------------
        @param self : object pointer
        """
        matt_id = self._context.get('active_id')
        ac_type = self.act_type
        ac_desc = self.descript
        close_date = self.date
        matter_close_rec = self.env['matter.matter'].browse(matt_id)
        if matter_close_rec:
            if ac_type == 'win':
                matter_close_rec.state = 'win'
                cases_won = matter_close_rec.sudo().assign_id.case_won
                cases_won += 1
                matter_close_rec.sudo().assign_id.case_won = cases_won
            if ac_type == 'lost':
                matter_close_rec.state = 'lost'
                cases_lost = matter_close_rec.sudo().assign_id.case_lost
                cases_lost += 1
                matter_close_rec.sudo().assign_id.case_lost = cases_lost
            if ac_type == 'settlement':
                matter_close_rec.state = 'settlement'
                cases_settle = matter_close_rec.sudo().assign_id.case_settle
                cases_settle += 1
                matter_close_rec.sudo().assign_id.case_settle = cases_settle
            case_assign = matter_close_rec.sudo().assign_id.case_assign
            case_assign -= 1
            matter_close_rec.sudo().assign_id.case_assign = case_assign
            matter_close_rec.is_close = True
            matter_close_rec.date_close = close_date
            act_obj = self.env['matter.close']
            act_vals = {
                'result_date': close_date,
                'result_type': ac_type,
                'result_descript': ac_desc,
                'mat_close_id': matter_close_rec.id,
            }
            act_obj.create(act_vals)
        mat_history_vals = {
            'name': dict(matter_close_rec._fields.get('state').
                         selection).get(matter_close_rec.state),
            'hist_date': close_date,
            'history_id': matter_close_rec.id,
        }
        matter_close_rec.matter_history_ids = [(0, 0, mat_history_vals)]
