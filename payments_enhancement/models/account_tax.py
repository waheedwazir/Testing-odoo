# -*- coding: utf-8 -*-

from odoo import fields, models


class accountTax(models.Model):
    _inherit = 'account.tax'

    sales_income_wht = fields.Selection([('sales_WHT', 'Sales WHT'), ('income_WHT', 'Income WHT')],
                                        string='Withholding Tax Type')