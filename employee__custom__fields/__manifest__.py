# -*- coding: utf-8 -*-
{
    'name': "Employee Custom Fields",
    'summary': """
        This Module allow to add on Employee profile, bellow information.
            1. Previous, Current and Total Experience fields
            2. Create a note book of Additional Information allow to record bellow data,
                    
            i. Current Address 
            ii. Permanent Address
            iii. Blood Group
            iv. EOBI No.
        """,

    'author': "Numdesk",
    'website': "http://www.numdesk.com",


    'depends': ['base', 'hr', 'hr_skills'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/data.xml',
        'security/security.xml',


        # 'views/hobbies.xml',
    ],
}
