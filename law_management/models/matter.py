# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import (DEFAULT_SERVER_DATE_FORMAT,
                        DEFAULT_SERVER_DATETIME_FORMAT)


def _desk_user(self):
    """This method will restrict duplication access for help desk manager"""
    user = self.env.user
    if user.has_group('law_management.group_law_erp_help_desk_officer'):
        raise UserError(_('Sorry, You cannot Duplicate a Record!'))


class Matter(models.Model):

    _name = 'matter.matter'
    _description = 'Matters'

    matter_seq = fields.Char('Matter ID')
    name = fields.Char('Matter Name')
    type = fields.Selection([('criminal', 'Criminal'), ('civil', 'Civil')],
                            string='Matter Type')
    category_id = fields.Many2one('matter.category', 'Category',
                                  ondelete='restrict')
    assign_id = fields.Many2one('hr.employee', 'Assign to')
    description = fields.Html('Description')
    article_ids = fields.Many2many('article.article', string='Article')
    act_ids = fields.Many2many('act.act', string='Acts')
    law_id = fields.Many2one('hr.employee', string='Lawyer')
    prac_area = fields.Many2many('matter.specialize', string='Practice Area')
    date_open = fields.Date('Opened Date')
    date_close = fields.Date('Closed Date')
    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approve'),
                              ('progress', 'In Progress'), ('win', 'Won'),
                              ('lost', 'Lost'), ('settlement', 'Settlement'),
                              ('re_open', 'Re open')], default='draft')
    evidence_count = fields.Integer(compute='_compute_evidence_count')
    trial_count = fields.Integer(compute='_compute_trial_count')
    evidence_count1 = fields.Integer(compute='_compute_evidence_count')
    trial_count1 = fields.Integer(compute='_compute_trial_count')
    matter_trial_id = fields.Many2one('matter.trial', 'Matter Trial')
    trial_date = fields.Date('Trial Date')
    trial_desc = fields.Text('Trial Description')
    opposition_ids = fields.One2many('matter.opposition', 'opposition_id',
                                     'Opposition')
    mat_contact = fields.One2many('matter.contact', 'contact_id',
                                  'Contact Person Details')
    mat_doc_ids = fields.One2many('matter.doc', 'doc_id', 'Matter Documents')
    mat_result_ids = fields.One2many('matter.close', 'mat_close_id',
                                     string='Matter Close Details')
    mat_client = fields.Many2one('res.partner', 'Client Name')
    location = fields.Char('Location')
    date = fields.Datetime('Date')
    attack_ids = fields.Many2many('criminal.attack', string='Attack Type')
    weapon = fields.Char('Weapons')
    death = fields.Integer('Total No of Deaths')
    victim_ids = fields.One2many('matter.victim', 'victim_id',
                                 string='Victims')
    perpeterator_ids = fields.One2many('matter.perpetrator', 'perpeterator_id',
                                       string='Perpetrators')
    suspect_ids = fields.One2many('matter.suspect', 'suspect_id', 'Suspects')
    pay_type = fields.Selection([('pay_per_hour', 'By Hour'),
                                 ('pay_per_trial', 'By Trial'),
                                 ('pay_per_fixed', 'By Fixed')],
                                string='Payment Type')
    matter_reopen_ids = fields.One2many('matter.reopen.wizard', 'reopen_id',
                                        'Reopen')
    reopen_date = fields.Date('Re-Open Date')
    invoice_id = fields.Many2one('account.move', 'Invoice')
    matter_history_ids = fields.One2many('matter.history', 'history_id',
                                         string='Matter History')
    is_reopen = fields.Boolean('Is reopened')
    is_close = fields.Boolean('Is Closed')
    invoice_count = fields.Float(compute='_compute_invoice_count',
                                 string='No. of Invoices')

    def _compute_invoice_count(self):
        """
        This method will count number of invoices of current matter.
        -------------------------------------------------------------
        """
        matter_invoice_obj = self.env['account.move']
        for matter in self:
            matter.invoice_count = matter_invoice_obj.search_count(
                [('matter_id', '=', matter.id)])

    @api.onchange('assign_id')
    def onchange_assign_id(self):
        """
        This method will set practice area of related lawyer.
        -------------------------------------------------------------
        """
        if self.assign_id:
            self.prac_area = self.assign_id.spec_ids or False

    def update_lawyer_clients(self, kw):
        matter_id = kw.get('matter_id')
        client_id = matter_id.mat_client
        assign_id = matter_id.assign_id
        if assign_id and client_id:
            user_id = matter_id.sudo().assign_id.user_id
            if user_id:
                c_ids = list()
                if user_id.client_ids:
                    for c_id in user_id.client_ids:
                        c_ids.append(c_id.id)
                if client_id.id not in c_ids:
                    c_ids.append(client_id.id)
                    user_id.sudo().write({'client_ids': [(6, 0, c_ids)]})
                old_client = kw.get('old_client')
                if old_client:
                    if old_client.id in c_ids:
                        matter_count = self.search([
                            ('assign_id', '=', assign_id.id),
                            ('mat_client', '=', old_client.id), ])
                        if not matter_count:
                            c_ids.remove(old_client.id)
                            user_id.sudo().write({'client_ids':
                                                  [(6, 0, c_ids)]})

    @api.onchange('type')
    def onchange_type(self):
        for rec in self:
            if rec.type:
                rec.attack_ids = [(5,)]

    @api.constrains('date_open')
    def check_date_open(self):
        """
        This method is used to validate the open date.
        ----------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        for rec in self:
            if rec.date_open > fields.Date.today():
                raise ValidationError(_('Open Date should be'
                                        ' less than the Current Date!'))

    @api.constrains('description')
    def check_description(self):
        """
        This method is used to validate for blank description.
        ------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        for rec in self:
            if not rec.description:
                raise ValidationError(_('Please add Description for matter.'))

    @api.model
    def create(self, vals):
        """
        This method will create sequence of the matter.
        -----------------------------------------------
        """
        vals.update({'matter_seq': self.env['ir.sequence'].
                     next_by_code('matter.matter')})
        res_id = super(Matter, self).create(vals)
        self.update_lawyer_clients({'matter_id': res_id})
        if res_id:
            mat_history_vals = {
                'name': dict(res_id._fields.get('state').
                             selection).get(res_id.state),
                'hist_date': fields.Date.today(),
                'history_id': res_id.id,
            }
        self.env['matter.history'].create(mat_history_vals)
        return res_id

    def write(self, vals):
        """
        This method will update the clients of assigned lawyer.
        -----------------------------------------------
        """
        res_id = super(Matter, self).write(vals)
        for rec in self:
            old_client = rec.mat_client
            kw = {'matter_id': rec,
                  'old_client': old_client}
            rec.update_lawyer_clients(kw)
        return res_id

    def matter_close(self):
        """
        This method is used to validation invoice of matter.
        --------------------------------------
        @param self: object pointer
        """
        if self.pay_type == 'pay_per_hour' or self.pay_type == 'pay_per_fixed':
            if not self.invoice_id:
                raise UserError(_("Can't close the Matter without"
                                " creating invoice!"))
        if self.pay_type == 'pay_per_trial':
            trail_obj = self.env['matter.trial']
            trail_ids = trail_obj.search([('matter_id', '=', self.id)])
            for trail_id in trail_ids:
                if not trail_id.tri_invoice_id:
                    raise UserError(_("Can't close the Matter without"
                                      " creating invoice for"
                                      " trails(%s)!") % str(trail_id.trial_seq)
                                    )
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Matter Close'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'matter.close.wizard',
            'src_model': 'matter.matter',
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'}

    def create_invoice_matter(self):
        """
        This method is used to create invoice.
        --------------------------------------
        @param self: object pointer
        """
        if self.pay_type == 'pay_per_hour':
            context = dict(self.env.context or {})
            context['active_id'] = self.id
            return {
                'name': _('Work Hour'),
                'view_mode': 'form',
                'res_model': 'matter.work.hour',
                'src_model': 'matter.matter',
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'new'}
        if self.pay_type == 'pay_per_fixed':
            invoice_line_vals = []
            cr_dt = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            inv_obj = self.env['account.move']
            is_invoice_exits = inv_obj.search_count(
                [('matter_id', '=', self.id)])
            if is_invoice_exits:
                raise UserError(_("Invoice is created already"
                                " against this Matter!"))
            if not is_invoice_exits:
                journal_id = inv_obj.with_context(
                    default_move_type='out_invoice')._get_default_journal()
                inv_line_vals = {
                    'name': self.name,
                    'price_unit': self.assign_id.fees_fixed,
                    'account_id': journal_id and
                    journal_id.default_account_id and
                    journal_id.default_account_id.id
                    or False, }
                invoice_line_vals.append((0, 0, inv_line_vals))
                inv_vals = {
                    'partner_id': self.mat_client and
                    self.mat_client.id or False,
                    'invoice_date': cr_dt,
                    'user_id': self.assign_id and self.assign_id.user_id and
                    self.assign_id.user_id.id or False,
                    'matter_id': self and self.id or False,
                    'pay_type': 'pay_per_fixed',
                    'move_type': 'out_invoice',
                    'state': 'draft',
                    'journal_id': journal_id and journal_id.id or False,
                    'invoice_line_ids': invoice_line_vals, }
                inv_id = self.env['account.move'].create(inv_vals)

                inv_id._onchange_partner_id()
                self.invoice_id = inv_id and inv_id.id

    def _compute_evidence_count(self):
        """
        This method is used to calculate total number of evidence.
        ---------------------------------------------------------
        """
        evidence_obj = self.env['matter.evidence']
        for matter in self:
            matter.evidence_count = evidence_obj.search_count(
                [('matter_id', '=', matter.id)])
            matter.evidence_count1 = evidence_obj.search_count(
                [('matter_id', '=', matter.id)])

    def _compute_trial_count(self):
        """
        This method is used to calculate total number of trials.
        --------------------------------------------------------
        """
        trial_obj = self.env['matter.trial']
        for matter in self:
            matter.trial_count = trial_obj.search_count(
                [('matter_id', '=', matter.id)])
            matter.trial_count1 = trial_obj.search_count(
                [('matter_id', '=', matter.id)])

    def unlink(self):
        """
        This method will raise warning user delete matter not in draft state.\
        ----------------------------------------------------------------------
        @param self : object pointer
        """
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('You cannot delete the matter that'
                                        ' have progressed beyond Draft state'))
        return super(Matter, self).unlink()

    def change_approve(self):
        """
        This method will change the state of matter to approve state and will\
        create history of matter.
        -------------------------------------------------------------
        """
        for rec in self:
            rec.state = 'approve'
            mat_history_vals = {
                'name': dict(rec._fields.get('state').selection).
                get(rec.state),
                'hist_date': fields.Date.today(),
                'history_id': rec.id,
            }
            rec.matter_history_ids = [(0, 0, mat_history_vals)]
            if not rec.is_reopen:
                cases_assign = rec.assign_id and \
                    rec.sudo().assign_id.case_assign
                cases_assign += 1
                rec.assign_id.case_assign = cases_assign

    def change_in_progress(self):
        """
        This method will change the state to progress state and will create \
        history of matter.
        ---------------------------------------------------------------------
        """
        for rec in self:
            rec.state = 'progress'
            mat_history_vals = {
                'name': dict(rec._fields.get('state').selection).
                get(rec.state),
                'hist_date': fields.Date.today(),
                'history_id': rec.id,
            }
            rec.matter_history_ids = [(0, 0, mat_history_vals)]

    def open_evidence(self):
        self.ensure_one()
        ctx = self.env.context
        active_id = ctx.get("active_id")
        evidence_tree = self.env.ref(
            'law_management.matter_evidence_view_tree').id
        evidence_form = self.env.ref(
            'law_management.matter_evidence_view_form').id
        return {
            'name': "Matter Evidence",
            'type': "ir.actions.act_window",
            'res_model': "matter.evidence",
            'view_mode': "tree,form",
            'view_ids': [(5, 0, 0),
                         (0, 0, {'view_mode': 'tree',
                                 'view_id': evidence_tree}),
                         (0, 0, {'view_mode': 'form',
                                 'view_id': evidence_form})],
            'domain': [('matter_id', '=', self.id)],
            'context': {
                'search_default_matter_id': [active_id],
                'default_matter_id': active_id,
            }
        }

    def open_trial(self):
        self.ensure_one()
        ctx = self.env.context
        active_id = ctx.get("active_id")
        trial_tree = self.env.ref(
            'law_management.matter_trial_view_tree').id
        trial_form = self.env.ref(
            'law_management.matter_trial_view_form').id
        return {
            'name': "Matter Trial",
            'type': "ir.actions.act_window",
            'res_model': "matter.trial",
            'view_mode': "tree,form",
            'view_ids': [(5, 0, 0),
                         (0, 0, {'view_mode': 'tree',
                                 'view_id': trial_tree}),
                         (0, 0, {'view_mode': 'form',
                                 'view_id': trial_form})],
            'domain': [('matter_id', '=', self.id)],
            'context': {
                'search_default_matter_id': [self.id],
                'default_matter_id': self.id,
            }
        }


class MatterType(models.Model):

    _name = 'matter.category'
    _description = 'matter type'

    type = fields.Selection([('criminal', 'Criminal'), ('civil', 'Civil')],
                            string='Category Type')
    name = fields.Char('Name')
    code = fields.Char('Code')

    def unlink(self):
        """
        This method will raise warning user \
        delete matter category assigned in matter.\
        ----------------------------------------------------------------------
        @param self : object pointer
        """
        for rec in self:
            mat_ids = self.env['matter.matter'].search_count(
                [('category_id', '=', rec.id)])
            if mat_ids:
                raise ValidationError(_('You cannot delete the categories'
                                        ' that have assigned to matter!'))
        return super(MatterType, self).unlink()

    def copy(self, default=None):
        """
        This method will restrict duplication access for help desk manager
        ----------------------------------------------------
        @param self : object pointer
        """
        self.ensure_one()
        _desk_user(self)
        return super(MatterType, self).copy(default=default)


class MatterOpposition(models.Model):

    _name = 'matter.opposition'
    _description = 'Matter Opposition'

    opposition_id = fields.Many2one('matter.matter', 'Opposition Id')
    name = fields.Many2one('opposition.lawyer', 'Opposition Party',
                           domain=[('type', '=', 'client')])
    cli_contact = fields.Char(related='name.contact_no',
                              string='Opposition Party Contact No')
    oppo_lawyer = fields.Many2one('opposition.lawyer',
                                  string='Opposition Lawyer',
                                  domain=[('type', '=', 'lawyer')])
    opp_contact = fields.Char(related='oppo_lawyer.contact_no',
                              string='Opposition lawyer Contact No')


class MatterContact(models.Model):

    _name = 'matter.contact'
    _description = 'Matter Contact'

    contact_id = fields.Many2one('matter.matter', 'Matter Contact')
    name = fields.Char('Name')
    address = fields.Text('Address')
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State',
                               ondelete='restrict')
    country_id = fields.Many2one('res.country', string='Country',
                                 ondelete='restrict')
    matt_contact = fields.Char('Contact No')
    comments = fields.Text('Statement')
    image = fields.Binary('Image')

    @api.constrains('image')
    def validate_mobile_image(self):
        """
        Raise a Validation Error if user enters invalid contact no.
        -----------------------------------------------------------
        """
        for obj in self:
            if not obj.image:
                raise ValidationError(_("Please add Image For Contact Person"
                                      " Detail in Matter!"))

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            return {'domain': {'state_id': [('country_id', '=',
                                             self.country_id.id)]}}
        return {'domain': {'state_id': []}}


class MatterDoc(models.Model):

    _name = 'matter.doc'
    _description = 'Matter Documents'

    doc_id = fields.Many2one('matter.matter', 'Matter Documents')
    mat_doc_attach_id = fields.Many2many('ir.attachment', string='Attachments')
    comment = fields.Text('Description')


class MatterClose(models.Model):
    _name = 'matter.close'
    _description = 'Matter Close'

    mat_close_id = fields.Many2one('matter.matter', 'Matter close')
    result_date = fields.Date('Result Date')
    result_descript = fields.Text('Result Description')
    result_type = fields.Selection([('win', 'Win'), ('lost', 'Lost'),
                                    ('settlement', 'Settlement')],
                                   string='Result Type')


class CriminalAttack(models.Model):
    _name = 'criminal.attack'
    _description = 'Types of criminal attack'

    matter_id = fields.Many2one('matter.matter', 'Matter')
    name = fields.Char('Name')
    code = fields.Char('Code')
    attack_type = fields.Selection(related='matter_id.type',
                                   string='Matter Type')


class MatterVictim(models.Model):
    _name = 'matter.victim'
    _description = 'Matter Victim'

    victim_id = fields.Many2one('matter.matter', 'victims')
    name = fields.Char('Name')


class MatterPerpetrator(models.Model):
    _name = 'matter.perpetrator'
    _description = 'Matter Perpetrator'

    perpeterator_id = fields.Many2one('matter.matter', 'Perpetrator')
    name = fields.Char('Name')


class MatterSuspect(models.Model):
    _name = 'matter.suspect'
    _description = 'Matter Suspect'

    suspect_id = fields.Many2one('matter.matter', 'Suspect')
    name = fields.Char('Suspect name')
    note = fields.Text('Description')
    image = fields.Binary('Image')


class MatterJudge(models.Model):
    _name = 'matter.judge'
    _description = 'Matter Judge Details'

    name = fields.Char('Judge Name')
    phone = fields.Char('Contact No')

    def copy(self, default=None):
        """
        This method will restrict duplication access for
        help desk manager
        ------------------------------------------------
        @param self : object pointer
        """
        self.ensure_one()
        _desk_user(self)
        return super(MatterJudge, self).copy(default=default)


class MatterHistory(models.Model):
    _name = 'matter.history'
    _description = 'Matter History'

    history_id = fields.Many2one('matter.matter', 'History')
    name = fields.Char('State')
    hist_date = fields.Date('Date')
    reason = fields.Text('Reason')


class MatterEvidence(models.Model):
    _name = 'matter.evidence'
    _description = 'Evidence of the matter'

    matter_id = fields.Many2one('matter.matter', string='Matter')
    evi_seq = fields.Char('Evidence ID')
    name = fields.Char('Evidence Name')
    evi_description = fields.Text('Description')
    evi_attachment_id = fields.Many2many('ir.attachment', string='Attachments')
    evi_in_favor = fields.Selection([('client', 'Client'),
                                     ('opposition', 'Opposition')],
                                    string='Evidence in Favor')

    @api.model
    def create(self, vals):
        """
        This method will create sequence for evidence.
        ----------------------------------------------
        """
        matter_id = self._context.get('active_id')
        evi_sequence = self.env['ir.sequence'].next_by_code('matter.evidence')
        vals.update({'evi_seq': evi_sequence, 'matter_id': matter_id})
        return super(MatterEvidence, self).create(vals)

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(MatterEvidence, self).fields_view_get(view_id=view_id,
                                                          view_type=view_type,
                                                          toolbar=toolbar,
                                                          submenu=submenu)
        context = self.env.context
        not_create = context.get('user_evidence')
        if not_create:
            doc = etree.XML(res['arch'])
            for t in doc.xpath("//"+view_type):
                t.attrib['create'] = 'false'
            res['arch'] = etree.tostring(doc)
        return res


class MatterTrial(models.Model):
    _name = 'matter.trial'
    _description = 'Matter Trial'
    _order = 'date desc'

    matter_id = fields.Many2one('matter.matter', 'Matter')
    pay_type = fields.Selection(related='matter_id.pay_type',
                                string='Payment Type')
    trial_seq = fields.Char('Trial ID')
    name = fields.Char('Trial Name')
    date = fields.Date('Trial Date')
    description = fields.Text('Notes')
    court_name = fields.Many2one('court.court', 'Court Name')
    court_location = fields.Char(related='court_name.location',
                                 string='Court Location')
    judge_name = fields.Many2one('matter.judge', 'Judge Name')
    trial_invoice = fields.Char('Trial Invoice')
    tri_invoice_id = fields.Many2one('account.move', 'Invoice')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'),
                              ('close', 'Close')], default='draft')
    trial_result = fields.Text('Trial Result')
    is_invoice = fields.Boolean('Is Invoiced')
    result = fields.Float('Result in %')

    @api.constrains('result')
    def check_result(self):
        '''
        This method is used to validate the trial result in %.
        ---------------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        for rec in self:
            if rec.result:
                if rec.result > 100 or rec.result <= 0:
                    raise ValidationError(_('Result should be in range between'
                                            ' 1 to 100!'))

    @api.constrains('date', 'result')
    def check_trial_date(self):
        '''
        This method is used to validate the trial date and result in %.
        ---------------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        for rec in self:
            if rec.matter_id.date_open and rec.date:
                if rec.date <= rec.matter_id.date_open:
                    raise ValidationError(_('Trial Date should be greater than'
                                            ' the Open Date of Matter!'))
            if rec.matter_id.reopen_date:
                if rec.date <= rec.matter_id.reopen_date:
                    raise ValidationError(_('Trial Date should be greater than'
                                            ' the Re-Open Date of Matter!'))

    def update_trail_seq(self, matter_id):
        if matter_id:
            trail_id = self.search(
                [('matter_id', '=', matter_id)],
                limit=1,
                order='trial_seq desc')
            if trail_id.trial_seq:
                trial_seq = (trail_id.trial_seq).split('/')
                trial_seq = int(trial_seq[-1]) + 1
            else:
                trial_seq = '1'
            matter_id = self.env['matter.matter'].browse(matter_id)
            if matter_id:
                trial_seq = str(matter_id.matter_seq) + '/Trial/' + str(trial_seq)
                return trial_seq

    @api.model
    def create(self, vals):
        '''
        This method is used to create sequence of trial.
        ------------------------------------------------
        @param self: object pointer
        @return: sequence of trial
        '''
        matter_id = self._context.get('active_id')
        trial_date = vals.get('date', False)
        vals.update({'trial_seq': self.update_trail_seq(
            matter_id), 'matter_id': matter_id})

        for rec in self.search([('matter_id', '=', matter_id)]):
            if rec.matter_id.pay_type == 'pay_per_trial':
                if not rec.tri_invoice_id:
                    raise UserError(_(
                        "Can't create the Trail without"
                        " creating invoice for trails(%s)!") %
                        str(rec.trial_seq))
            if rec.state in ['draft', 'open']:
                raise ValidationError(_('You cannot create multiple'
                                        ' trials at same time.'))
            if rec.date == trial_date:
                raise ValidationError(_('You cannot create multiple'
                                        ' trials at same date!'))
        # Max date checking
        max_date = self.search([('matter_id', '=', matter_id)], limit=1,
                               order='date desc')
        if trial_date and max_date and trial_date < str(max_date.date):
            raise ValidationError(_('Trial Date should be greater than'
                                    ' previous trial date.'))
        trial = super(MatterTrial, self).create(vals)
        trial.matter_id.trial_date = trial_date
        return trial

    def create_invoice_trial(self):
        """
        This method is used to create invoice.
        --------------------------------------
        @param self: object pointer
        """
        cr_dt = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        inv_obj = self.env['account.move']
        inv_line_obj = self.env['account.move.line']
        for rec in self:
            if not rec.tri_invoice_id:
                journal_id = inv_obj.with_context(
                    default_move_type='out_invoice')._get_default_journal()
                inv_vals = {
                    'partner_id': rec.matter_id.mat_client and
                    rec.matter_id.mat_client.id or False,
                    'invoice_date': cr_dt,
                    'user_id': rec.matter_id.assign_id
                    and rec.matter_id.assign_id.user_id and
                    rec.matter_id.assign_id.user_id.id or False,
                    'trial_id': rec.id,
                    'matter_id': rec.matter_id and rec.matter_id.id
                    or False,
                    'pay_type': 'pay_per_trial',
                    'move_type': 'out_invoice',
                    'state': 'draft',
                    'journal_id': journal_id and journal_id.id or False,
                    'invoice_line_ids':[(0,0,{
                      'name': rec.name,
                      'price_unit': rec.matter_id.assign_id.fees_trial,
                      'account_id': journal_id and journal_id.default_account_id and journal_id.default_account_id.id or False,
                     })]
                }
                inv_id = inv_obj.create(inv_vals)
                rec.is_invoice = True
                inv_id._onchange_partner_id()
                rec.tri_invoice_id = inv_id and inv_id.id or False

    def unlink(self):
        """
        Override method to restrict the deletion of the won,lost, settled
        trials.
        """
        if self.filtered(lambda rec: rec.matter_id.state in
                         ['win', 'lost', 'settlement']):
            raise ValidationError(
                _('You cannot delete trials in closed matter!'))
        return super(MatterTrial, self).unlink()

    def trial_open(self):
        """
        This method will change the state to Open state.
        ------------------------------------------------
        """
        for rec in self:
            rec.state = 'open'

    def trial_close(self):
        """
        This method will change the state to Close state.
        ---------------------------------------------------
        """
        for rec in self:
            if rec.date > fields.Date.today():
                raise ValidationError(_('You can not done the future Trial'
                                        ' record!'))
            else:
                rec.state = 'close'

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(MatterTrial, self).fields_view_get(view_id=view_id,
                                                       view_type=view_type,
                                                       toolbar=toolbar,
                                                       submenu=submenu)
        context = self.env.context
        not_create = context.get('user_trial')
        if not_create:
            doc = etree.XML(res['arch'])
            for t in doc.xpath("//"+view_type):
                t.attrib['create'] = 'false'
            res['arch'] = etree.tostring(doc)
        return res


class MatterSpecialize(models.Model):
    _name = 'matter.specialize'
    _description = 'Matter Specialization'

    name = fields.Char('Name')
    code = fields.Char('Code')
    spec_type = fields.Selection([('criminal', 'Criminal'),
                                  ('civil', 'Civil')], string='Specialization')

    def copy(self, default=None):
        """
        This method will restrict duplication access for help desk manager
        ----------------------------------------------------
        @param self : object pointer
        """
        self.ensure_one()
        _desk_user(self)
        return super(MatterSpecialize, self).copy(default=default)
