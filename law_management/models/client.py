# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import matter


class Client(models.Model):
    _inherit = 'res.partner'

    client_id = fields.Char('Client ID')
    cli_req_id = fields.Many2one('res.partner', 'client')
    part_type = fields.Selection([('lawyer', 'Lawyer'),
                                  ('client', 'Client')],
                                 string='Partner Type')
    client_type = fields.Selection([('client', 'Client'),
                                    ('opp_client', 'Opposition Client')],
                                   string='Client Type')
    emp_id = fields.Many2one('res.users', string='User')

    @api.constrains('image_1920')
    def _check_image(self):
        for rec in self:
            if rec.part_type == 'client' and not rec.image_1920:
                raise ValidationError(_('Please add image for Client.'))

    @api.constrains('email')
    def validate_email(self):
        """
        Raise a Validation Error when user enters incorrect email
        ---------------------------------------------------------
        """
        for obj in self:
            if obj.email \
                and re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|\
                    [0-9]{1,3})(\\]?)$", obj.email) is None:
                raise ValidationError(_(
                    """Please add valid Email Address:%s""" % obj.email))
        return True

    @api.model
    def create(self, vals):
        """
        This method is used to create sequence for the client
        -----------------------------------------------------
        @param self : object pointer
        @param vals : A dictionary containing keys and values
        """
        client_id_seq = self.env['ir.sequence'].next_by_code('client.number')
        vals.update({'client_id': client_id_seq or '',
                     'email': vals.get('email', '')})
        return super(Client, self).create(vals)


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    empl_id = fields.Many2one('hr.employee', 'Employee')

    @api.constrains('acc_number')
    def _check_acc_number(self):
        for rec in self:
            if re.match('^([0-9]{10,12})$', rec.acc_number) is None:
                raise ValidationError(_(
                    '''Please add Proper Bank account Number'''))


class ClientRequest(models.Model):
    _name = 'client.request'
    _description = 'Client Description'

    name = fields.Char('Name')
    contact_no = fields.Char('Contact No')
    email = fields.Char('Email', size=32)
    services = fields.Many2one('client.service', 'Services')
    mat_type = fields.Selection([('criminal', 'Criminal'), ('civil', 'Civil')],
                                string='Matter Type')
    note = fields.Text('Brief Description')
    state = fields.Selection([('draft', 'Draft'), ('request', 'Requested'),
                              ('approve', 'Approved'), ('reject', 'Rejected')],
                             default='draft')

    @api.constrains('email')
    def validate_email(self):
        """
        Raise a Validation Error when user enters incorrect email
        ---------------------------------------------------------
        """
        for obj in self:
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]\
            {1,3})(\\]?)$", obj.email) is None:
                raise ValidationError(_("Please add valid Email Address:"
                                        " %s" % obj.email))
        return True

    def change_draft(self):
        """
        This method will change the state to Draft state.
        ---------------------------------------------------
        """
        for rec in self:
            rec.state = 'draft'

    def change_request(self):
        """
        This method will change the state to Request state.
        ---------------------------------------------------
        """
        for rec in self:
            rec.state = 'request'

    def change_approve(self):
        """
        This method will change the state to Approve state.
        ---------------------------------------------------
        """
        user_obj = self.env['res.users']
        hr_officer = self.env.ref('hr.group_hr_user', False)
        for rec in self:
            if rec.state == 'request':
                user_vals = {
                    'name': rec.name or '',
                    'login': rec.email or '',
                    'user_type': 'client',
                    'part_type': 'client',
                    'email': rec.email or '',
                    'mobile': rec.contact_no or '',
                    'groups_id': [(6, 0, hr_officer.ids)],
                }
                user_obj.sudo().create(user_vals)
            rec.state = 'approve'

    def change_reject(self):
        """
        This method will change the state to Reject state.
        ---------------------------------------------------
        """
        for rec in self:
            rec.state = 'reject'

    def unlink(self):
        """
        This method will unlink the related user and partner
        ----------------------------------------------------
        @param self : object pointer
        """
        for client in self:
            if client.state != 'draft':
                raise ValidationError(_('You cannot delete client request '
                                        'progressed beyond "Draft" state'))
        return super(ClientRequest, self).unlink()


class ClientService(models.Model):
    _name = 'client.service'
    _description = 'Client Service'

    name = fields.Char('Name')
    code = fields.Char('Code')

    def copy(self, default=None):
        """
        This method will restrict duplication access for help desk manager
        ----------------------------------------------------
        @param self : object pointer
        """
        self.ensure_one()
        matter._desk_user(self)
        return super(ClientService, self).copy(default=default)


class ResUser(models.Model):
    _inherit = 'res.users'

    user_type = fields.Selection([('lawyer', 'Lawyer'),
                                  ('client', 'Client')],
                                 string='User Type')
    client_ids = fields.Many2many('res.partner', string='Clients')


class ResCompany(models.Model):
    _inherit = 'res.company'

    countable_exp_percent = fields.Float("Countable (%) of Experience",
                                         default=100.0,
                                         help='Countable \
                                          experience of Employee \
                                          will be calculated based \
                                          on this percentage')
