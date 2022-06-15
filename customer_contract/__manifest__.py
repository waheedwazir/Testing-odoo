# -*- coding: utf-8 -*-
{
    'name': "Customer Contract",

    'summary': """
        This module is for customer contract management.""",

    'description': """
        This module is for customer contract management
    """,

    'author': "Numdesk",
    'website': "http://www.numdesk.com",
    'category': 'Uncategorized',
    'version': '0.1',
   'depends': ['base', 'mail'],


    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/bank_account.xml',
        'views/templates.xml',
        'reports/report.xml',
        'reports/customer_contract_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
