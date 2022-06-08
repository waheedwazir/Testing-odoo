# -*- coding: utf-8 -*-

from odoo import models, fields, api


class raynpayslip(models.Model):
    _inherit = 'hr.payslip'


    def rayn_report_payslip(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'rayn_payslip.rayn_payslip_report',
            'model': 'hr.payslip',
            'report_type': "qweb-pdf"
        }

class SalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    section = fields.Selection(
        string='Salary Rule Section',
        selection=[('pay_earing', 'Pay Period Earning'),
                   ('pay_year_to_date', 'Pay Year to Date'), ],
         help='Used to display salary rules section' )






