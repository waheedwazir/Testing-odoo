# -*- coding: utf-8 -*-
{
    'name': "Tax Localization",

    'summary': """
        Allows you to apply taxes on payment based on slabs""",

    'author': "Num Desk",
    'website': "https://www.numdesk.com",

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'payments_enhancement', 'account_reports'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/rent_contract.xml',
        'views/templates.xml',
        'report/wizard.xml',
    ],
}
