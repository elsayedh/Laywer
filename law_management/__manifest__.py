# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Law and Legal Practices Management',
    'version': '14.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Law Management',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['hr', 'account'],
    'summary': '''Law Management, Legal Management,
        This module allows to manage lawyers,clients,
        matters(cases), trials and its invoicing.''',
    'contributors': [
        'Serpent Consulting Services Pvt. Ltd.'
    ],
    'data': [
        'security/law_management_security.xml',
        'security/ir.model.access.csv',
        'demo/lawerp_demo.xml',
        'data/sequence.xml',
        'wizard/wiz_button_close.xml',
        'wizard/wiz_work_hour.xml',
        'wizard/wiz_button_reopen.xml',
        'views/invoice.xml',
        'views/evidence_trial.xml',
        'views/matter.xml',
        'views/res_users.xml',
        'views/lawyer.xml',
        'views/client.xml',
        'views/act_article.xml',
        # 'report/matter_analysis.xml',
        'report/qweb_report_registration.xml',
        'report/report_matter.xml',
        'report/report_lawyer.xml',
    ],
    'images': ['static/description/LawManagement.png'],
    'external_dependencies': {'python': ['matplotlib', 'numpy']},
    'installable': True,
    'application': True,
    'price': 30,
    'currency': 'EUR'
}
