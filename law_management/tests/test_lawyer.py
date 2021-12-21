from odoo.tests import common
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class TestHrEmployee(common.TransactionCase):
    """Test Case for lawyer."""

    def setUp(self):
        """Initialize School Test Cases."""
        super(TestHrEmployee, self).setUp()
        dt = datetime.strptime('1999-6-19',DF)
        lawayer_rec = ({'birthday':dt,'fees_hour':20,'name':'mahi',
            'mobile_phone':'70430244545','work_email':'m@gmail.com',
            'employment_date':'2014-01-01'})
        self.lawyer1 = self.env['hr.employee'].create(lawayer_rec)
        self.lawyer1._compute_set_age()
        
    def test_compute_calc_curr_experience(self):
        self.lawyer1._compute_calc_curr_experience()
        self.assertFalse(self.lawyer1.current_exp)
        
    def test__compute_calc_total_exp(self):
        lawyer2 = self.lawyer1.write({'current_exp':20,'previous_exp':20,'gap':10})
        self.lawyer1._compute_calc_total_exp()
        self.assertFalse(self.lawyer1.total_exp)

    def test__compute_calc_countable_exp(self):
        lawyer3 = self.lawyer1.write({'current_exp':20,'previous_exp':20,'gap':10})
        self.lawyer1._compute_calc_countable_exp()
        self.assertFalse(self.lawyer1.countable_exp)

    def test_check_fees(self):
        lawyer_fees = {'fees_hour': 200,'is_lawyer':True,'fees_trial':00,'fees_fixed':120}
        with self.assertRaises(ValidationError):
            self.lawyer1.write(lawyer_fees)
            
    def test_validate_email(self):
        with self.assertRaises(ValidationError):
            self.lawyer1.validate_email()
