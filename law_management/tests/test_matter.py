from odoo.tests import common
from odoo.exceptions import ValidationError
from datetime import datetime

class TestMatterMatter(common.TransactionCase):

    def setUp(self):
        """Initialize School Test Cases."""
        super(TestMatterMatter, self).setUp()
        self.matter_vals = ({'date_open':'2021-3-15','description':'xyz'})
        self.matter1 = self.env['matter.matter'].create(self.matter_vals)
        
        self.trial1 = ({'name':'xyz','date':'2021-3-18','court_location':'dfd','matter_id':self.id})
        self.trial = self.env['matter.trial'].create(self.trial1)
      
    def test_check_date_open(self):
        with self.assertRaises(ValidationError):
            self.matter1.write(self.matter_vals)
            
    def test_check_description(self):
        with self.assertRaises(ValidationError):
                self.matter1.check_description()

    def test_onchange_assign_id(self):
        matter_record = ({'assign_id':1})
        self.matter1.write(matter_record)
        self.matter1.onchange_assign_id()
        self.assertFalse(self.matter1.prac_area)

    def test_onchange_type(self):
        matter_record = ({'type':'criminal'})
        self.matter1.write(matter_record)
        self.matter1.onchange_type()
        self.assertFalse(self.matter1.attack_ids)

    def test_matter_close(self):
        self.matter_type = ({'pay_type':'pay_per_hour'})
        self.matter1.write(self.matter_type)
        self.matter1.matter_close()
        self.assertFalse(self.matter1.invoice_id)


    def test_create_invoice_trial(self):
        self.matter1.create_invoice_trial()
        

    def test_compute_invoice_count(self):

        account_move_rec = ({'name':'xyz','matter_id':self.matter1.id,'date':'2021-3-16','state':'draft','move_type':'entry','journal_id':12,'currency_id':1})
        self.acount_record = self.env['account.move'].create(account_move_rec)
        self.matter1._compute_invoice_count()
        self.assertFalse(self.matter1.invoice_count)

    def test_compute_evidence_count(self):
        account_move_rec = ({'name':'xyz','matter_id':self.matter1.id})
        self.acount_record = self.env['matter.evidence'].create(account_move_rec)
        self.matter1._compute_evidence_count()
        self.assertFalse(self.matter1.evidence_count)

    def test_compute_trial_count(self):
        account_move_rec = ({'name':'xyz','matter_id':self.matter1.id})
        self.acount_record = self.env['matter.trial'].create(account_move_rec)
        self.matter1._compute_evidence_count()
        self.assertFalse(self.matter1.trial_count)

    def test_change_approve(self):
            mat_history_vals = {
                'name': 'xyz',
                'state':'approve',
            }
            self.matter_approve = self.env['matter.matter'].create(mat_history_vals)
            self.assertFalse(self.matter1.is_reopen)

    def test_change_in_progress(self):
        mat_history_vals = {
            'name':'maitri',
            'state':'progress',
        }
        self.matter_progress = self.env['matter.matter'].create(mat_history_vals)
        self.matter1.change_in_progress()
        self.assertFalse(self.matter1.is_reopen)

    def test_check_result(self):
        self.matter_vals = ({'result':100})
        self.matter1 = self.env['matter.trial'].create(self.matter_vals)
        with self.assertRaises(ValidationError):
            self.matter1.write(self.matter_vals)


    def test_check_trial_date(self):
        self.matter_vals = ({'date':'2021-3-17','matter_id':1})
        self.matter1 = self.env['matter.trial'].create(self.matter_vals)
        with self.assertRaises(ValidationError):
            self.matter1.write(self.matter_vals)


