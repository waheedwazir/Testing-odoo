# -*- coding: utf-8 -*-

from odoo import models, fields, api


class offerletterreport(models.Model):
    _inherit = 'hr.applicant'

    fuel_allowance = fields.Float(string='Fuel Allowance')
    internet_allowance = fields.Float(string='Internet Allowance')
    hospitalization = fields.Float(string='Hospitalization')
    opd_coverage = fields.Float(string='OPD Coverage')
    total_gross_salary = fields.Float('total_gross_salary',compute='compute_gross_salary', store=True)

    @api.depends('fuel_allowance','internet_allowance','salary_proposed')
    def compute_gross_salary(self):
        for rec in self:
            rec.total_gross_salary = (rec.fuel_allowance + rec.internet_allowance + rec.salary_proposed)



