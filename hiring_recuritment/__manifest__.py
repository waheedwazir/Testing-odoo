# -*- coding: utf-8 -*-
{
    'name': " Hiring Request ",

    'summary': """
        This module is developed for Hiring Request of Employees""",

    'author': "NumDesk",
    'website': "http://numdesk.com",
    # 'depends': ['base', 'mail', 'hr', 'hr_resignation'],
    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr', 'hr_resignation', 'offer_letter_report'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        'views/Position_status.xml',
        'views/data.xml',
        'Report/report.xml',
        'Report/report_temp.xml',
        'views/templates.xml',
    ],
}
