# -*- coding: utf-8 -*-
{
    'name': "Recruitment",

    'summary': """""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','hr_recruitment',],

    # always loaded
    'data': [
        'ir.model.access.csv',
        'model_view.xml',
        'tax_slab_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
