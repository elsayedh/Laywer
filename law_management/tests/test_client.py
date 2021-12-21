from odoo.tests import common
from odoo.exceptions import ValidationError

class TestResPartner(common.TransactionCase):
    """Test Case for lawyer."""
    def setUp(self):
        """Initialize School Test Cases."""
        super(TestResPartner, self).setUp()
        self.client_vals = {'name':'maitri','phone':70430244410,'mobile':1520,'email':'k@gmail.com'}
        self.client = self.env['res.partner'].create(self.client_vals)
       
    def test_client_validate_email(self):
        with self.assertRaises(ValidationError):
            self.client.validate_email()

class TestClientRequest(common.TransactionCase):

    def setup(self):
        super(TestClientRequest, self).setup()

    def test_validate_email(self):
        self.req_vals = {'email':'h@gamil.com','name':'xyz','contact_no':54511}
        self.client_req = self.env['client.request'].create(self.req_vals)
        with self.assertRaises(ValidationError):
            self.client_req.validate_email()

 