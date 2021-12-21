# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from lxml import etree

from . import matter


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.depends('employment_date')
    def _compute_calc_curr_experience(self):
        """
        This method is used to calculate the current experience
         based on the joining date
        -------------------------------------------------------
        @param self : object pointer
        """
        logn_term_month = 0
        for emp in self:
            if emp.employment_date:
                curr_exp = relativedelta(fields.Date.today(),
                                         emp.employment_date)
                emp.current_exp = (
                    curr_exp.years * 12
                ) + curr_exp.months - logn_term_month
            else:
                emp.current_exp = 0.0

    def _compute_calc_total_exp(self):
        """
        This method will calculate the total experience of a person having
        previous experience in other organizations and also the current
        experience in the organization
        ------------------------------------------------------------------
        @param self : object pointer
        """
        for emp in self:
            emp.total_exp = emp.current_exp + emp.previous_exp - emp.gap

    @api.depends('case_assign', 'case_won', 'case_lost', 'case_settle')
    def _compute_calc_total_case(self):
        """
        This method will calculate the total experience of a person having
        previous experience in other organizations and also the current
        experience in the organization
        ------------------------------------------------------------------
        @param self : object pointer
        """
        for emp in self:
            emp.tot_cases = emp.case_assign + emp.case_won + \
                emp.case_lost + emp.case_settle

    @api.depends('previous_exp', 'current_exp',
                 'employment_date', 'company_id', 'gap')
    def _compute_calc_countable_exp(self):
        """
        This method is used to calculate the countable experience for
        allocating the leaves.In this the previous experience will be
        calculated based on percentage specified in
        company configuration to allocate leaves by exp.
        ------------------------------------------------
        @param self : object pointer
        """
        for emp in self:
            comp_rec = emp and emp.company_id or False
            if not comp_rec:
                comp_rec = emp and emp.user_id and \
                    emp.user_id.company_id or False
            if comp_rec:
                emp.countable_exp = (emp.previous_exp *
                                     comp_rec.countable_exp_percent / 100
                                     ) + emp.current_exp - emp.gap

    def _search_countable_exp(self, operator, value):
        op_dict = {'=': '=', '<': '>', '>': '<', '<=': '>=', '>=': '<=',
                   '!=': '!=', '<>': '<>'}
        curr_date = datetime.now()
        j_dt = curr_date - relativedelta(months=value)
        jn_date = j_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        applicants = self.search([('employment_date',
                                   op_dict[operator],
                                   jn_date)])
        return [('id', 'in', applicants.ids)]

    previous_exp = fields.Float('Prev. Expr. (Months)',
                                help="Previous experience of an \
                                employee in another organization.")
    current_exp = fields.Float(compute='_compute_calc_curr_experience',
                               string='Curr. Expr. (Months)',
                               help="Current experience of an employee in this\
                               organization.")
    total_exp = fields.Float(compute='_compute_calc_total_exp',
                             string='Total. Expr. (Months)',
                             help="Total experience of an \
                              employee as of today.")
    countable_exp = fields.Float(string='Countable Experience (Months)',
                                 compute='_compute_calc_countable_exp',
                                 help='This will be used only for leave \
                                 allocation', search='_search_countable_exp')
    gap = fields.Float('Gap (Months)')
    case_assign = fields.Float('Assigned Cases')
    case_won = fields.Float('Won Cases')
    case_lost = fields.Float('Lost Cases')
    case_settle = fields.Float('Settled Cases')
    tot_cases = fields.Float(compute='_compute_calc_total_case', string='Total Cases',
                             store=True)
    l_image = fields.Binary("Employee Image", attachment=True, required=True,
                            help="This field holds the image used as photo for\
                             the employee, limited to 1024x1024px.")
    lawyer_id = fields.Char('Lawyer ID')
    is_lawyer = fields.Boolean(string='Is Lawyer?')
    qualification = fields.Selection([('LLB', 'LLB'),
                                      ('B.A. L.L.B', 'B.A. L.L.B'),
                                      ('L.L.M.', 'L.L.M.')], 'Qualification')
    spec_ids = fields.Many2many('matter.specialize', string='Practice Area')
    contact = fields.Char('Home Phone')
    employment_date = fields.Date('Employment Date',
                                  help='This will be the date when Employee\
                                        starts his Probation or Employment')
    acc_holder = fields.Char('Account Holder Name')
    birthday = fields.Date('Date of Birth')
    fees_hour = fields.Float('Fees Per Hour',
                             help="Amount will be charged by\
                             Lawyer charged per Hour.")
    fees_trial = fields.Float('Fees per Trial',
                              help="Amount will be charged by\
                              Lawyer charged per Trail.")
    fees_fixed = fields.Float('Fees Fixed',
                              help="Fixed amount will be Charged\
                              by Lawyer for a Matter.")
    age = fields.Integer(string="Age", compute='_compute_set_age')
    skills_ids = fields.One2many('emp.skills', 'skills_id', 'Skills')
    degree_ids = fields.One2many('emp.qualification', 'emp_id', 'Degree')
    certy_ids = fields.One2many(
        'emp.qualification', 'employee_id', 'Certificate')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(HrEmployee, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if self.user_has_groups("law_management.group_law_erp_lawyer"):
            for node in doc.xpath("//kanban"):
                node.set("create", 'false')
                node.set("edit", 'false')
            for node in doc.xpath("//tree"):
                node.set("create", 'false')
            for node in doc.xpath("//form"):
                node.set("create", 'false')
                node.set("edit", 'false')
        res['arch'] = etree.tostring(doc)
        return res

    def _active_languages(self):
        return self.env['res.lang'].search([]).ids

    @api.constrains('age', 'birthday')
    def check_age(self):
        """
        Raise Validation when age of Lawyer will be less than or equal to 18.
        ---------------------------------------------------------------------
        """
        for rec in self:
            if rec.is_lawyer:
                if rec.birthday >= fields.Date.today():
                    raise ValidationError(_('Date of Birth should be'
                                            ' less than the Current Date.'))
                if rec.age < 18:
                    raise ValidationError(_('Minimum age of'
                                            ' lawyer should be above 18!'))

    def _compute_set_age(self):
        age = 0
        for emp in self:
            if emp.birthday:
                age = relativedelta(fields.Date.today(), emp.birthday).years
            emp.age = age

    @api.constrains('fees_hour', 'fees_trial', 'fees_fixed')
    def check_fees(self):
        '''
        This method is used to validate the fees.
        -------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        for rec in self:
            if rec.is_lawyer and \
                (rec.fees_hour <= 0.0 or
                 rec.fees_trial <= 0.0 or
                 rec.fees_fixed <= 0.0):
                raise ValidationError(_('Invalid Lawyer Fees!'))

    @api.constrains('image_1920')
    def _check_image(self):
        for rec in self:
            if not rec.image_1920:
                raise ValidationError(_('Please add image for Lawyer.'))

    @api.constrains('work_email')
    def validate_email(self):
        """
        Raise a Validation Error when user enters incorrect email
        ---------------------------------------------------------
        """
        for obj in self:
            if obj.work_email and re.match(
                "^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]\
            {1,3})(\\]?)$", obj.work_email) is None:
                raise ValidationError(_("Please Provide valid Email Address:"
                                      " %s" % obj.work_email))
        return True

    def copy(self, default=None):
        if self.is_lawyer:
            raise ValidationError(_("Sorry you can\'t "
                                    "duplicate lawyer."))
        return super(HrEmployee, self).copy(default)

    @api.model
    def create(self, vals):
        lawyer_id_seq = self.env['ir.sequence'].next_by_code('hr.employee')
        vals.update({'lawyer_id': lawyer_id_seq})
        hr_officer = self.env.ref('hr.group_hr_user', False)
        res = super(HrEmployee, self).create(vals)
        user = False
        if res.is_lawyer:
            user_vals = {
                'name': vals.get('name', False),
                'login': vals.get('work_email', False),
                'email': vals.get('work_email', False),
                'phone': vals.get('work_phone', False),
                'mobile': vals.get('mobile_phone', False),
                'image_1920': vals.get('image_1920', False),
                'groups_id': [(6, 0, hr_officer.ids)],
                'user_type': 'lawyer',
                'part_type': 'lawyer',
            }
            user = self.env['res.users'].create(user_vals)
            res.write({'user_id': user and user.id or False})
        return res

    def write(self, vals):
        user_id = self.user_id.id or vals.get('user_id', False)
        user = self.env['res.users'].browse(self._context.get('uid'))
        if user and not user.has_group('law_management.group_law_erp_admin'):
            if user.id != user_id:
                raise UserError(_('Sorry, You cannot edit '
                                  'details of other Lawyers!'))
        return super(HrEmployee, self).write(vals)

    def unlink(self):
        """
        This method will unlink the related user and partner
        ----------------------------------------------------
        @param self : object pointer
        """
        for emp in self:
            if emp.case_assign > 0.0:
                raise ValidationError(_('You cannot delete lawyer assigned to'
                                        ' the matter'))
            if emp.user_id:
                partner = emp.user_id.partner_id
                emp.user_id.unlink()
                partner.unlink()
        return super(HrEmployee, self).unlink()


class OppositionLawyer(models.Model):
    _name = "opposition.lawyer"
    _description = 'Opposition Lawyer info'

    name = fields.Char()
    image = fields.Binary("Image")
    contact_no = fields.Char("Contact No.")
    no_case_won = fields.Integer("No of Cases won")
    no_case_lost = fields.Integer("No of Cases lost")
    prac_area = fields.Many2many("matter.specialize", string="Practice Area")
    type = fields.Selection([('lawyer', 'Lawyer'), ('client', 'Client')])

    def copy(self, default=None):
        """
        This method will restrict duplication access for
        lawyer and help desk manager
        ----------------------------------------------------
        @param self : object pointer
        """
        self.ensure_one()
        matter._desk_user(self)
        return super(OppositionLawyer, self).copy(default=default)


class EmpSkills(models.Model):
    _name = 'emp.skills'
    _description = 'Employee Skills'

    skills_id = fields.Many2one('hr.employee', 'skills')
    arg_approach = fields.Float('Argumentative Approach in %')
    language_id = fields.Many2one('res.lang', 'Language', required=True)


class LawDegree(models.Model):
    _name = "emp.degree"
    _description = "Lawyer Degree"

    name = fields.Char('Name')
    code = fields.Char("Code")
    type = fields.Selection([('degree', 'Degree'),
                             ('certificate', 'Certificate')], 'Type')

    def copy(self, default=None):
        """
        This method will restrict duplication access for help desk manager
        ----------------------------------------------------
        @param self : object pointer
        """
        self.ensure_one()
        matter._desk_user(self)
        return super(LawDegree, self).copy(default=default)


class EmpQualification(models.Model):
    _name = 'emp.qualification'
    _description = "Employee Qualification"
    _rec_name = "degree_id"

    institute_id = fields.Many2one('emp.institute', 'Institute')
    uni_id = fields.Many2one('emp.university', 'University')
    degree_id = fields.Many2one('emp.degree', 'Degree')
    certy_id = fields.Many2one('emp.degree', 'Certificate')
    passing_year = fields.Char('Year', size=4)
    emp_id = fields.Many2one('hr.employee', 'Employee')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    certy = fields.Binary(string='Document')
    file_name = fields.Char('File name')
    perc = fields.Float('Percentage')
    grade = fields.Char('Grade')

    @api.constrains('file_name')
    def check_document(self):
        """
        This method is used to validate the Document.
        ----------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        file_type = ['doc', 'pdf', 'docx', 'odt']
        for rec in self:
            if rec.file_name:
                f_name = (rec.file_name).split('.')
                if f_name[-1] not in file_type:
                    raise ValidationError(_("You can only attach"
                                          " the .doc, .pdf, .docx, .odt "
                                          "file formats."))


class EmpInstitute(models.Model):
    _name = 'emp.institute'
    _description = 'Employee Institute'

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
        return super(EmpInstitute, self).copy(default=default)


class EmpUniversity(models.Model):
    _name = 'emp.university'
    _description = 'Employee University'

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
        return super(EmpUniversity, self).copy(default=default)
