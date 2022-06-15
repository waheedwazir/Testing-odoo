# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class customer_contract(models.Model):
    _name = 'customer.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Many2one('res.partner' , required=1)
    phone = fields.Char(string="Phone No.",store=1 ,readonly=1)
    email = fields.Char(string="Email" ,store=1 , readonly=1)
    date_of_contract = fields.Date(
        string='Effective Date of Contract',
        required=False)
    start_date = fields.Date(
        string='Start Date',
        required=False)
    end_date = fields.Date(
        string='End Date',
        required=False)
    duration = fields.Char(string='Tenure', readonly=True, store=1)
    contract_price = fields.Integer(string='Contract Fees')
    currency = fields.Many2one('res.currency', string='Currency')
    customer_address = fields.Text(string="Address", compute="_compute_customer_address")
    entity = fields.Many2one('res.company',default=lambda self: self.env.company, string="Company")
    company_address = fields.Text(string="Address", compute="_compute_company_address" ,readonly=1)
    client_business = fields.Char(string="Client's Business Detail")
    terms_of_payment = fields.Char(string="Payment Terms")
    pocket_limit = fields.Integer(string="Out of Pocket Limit")

    account_no = fields.Many2one('bank.account', 'Account No')
    bank_title = fields.Char('Bank Title',readonly=1)
    iban = fields.Char('IBAN',readonly=1 ,store=1)
    swift_code = fields.Char('Swift Code',readonly=1 ,store=1)
    client_representative = fields.Char(string='Client Representative')
    client_position = fields.Char(string='Position')

    billing_nature = fields.Selection(
        string='Billing Nature',
        selection=[('monthly', 'Monthly'),
                   ('milestone', 'Milestone'), ],
        required=False)
    origin = fields.Selection(
        string='Origin',
        selection=[('local', 'Local'),
                   ('export', 'Export'), ],
        required=False)
    territory = fields.Selection(
        string='Territory',
        selection=[('sindh', 'Sindh'),
                   ('federal', 'Federal'),
                   ('punjab', 'Punjab'),
                   ('balochistan', 'Balochistan'),
                   ('kpk', 'Kpk '),
                   ('corporate entities', 'Corporate Entities'),
                   ('others', 'Others'), ],
        required=False)

    @api.onchange('entity')
    def _compute_company_address(self):
        for rec in self:
            res = [rec.entity.street,
                   rec.entity.street2,
                   rec.entity.city,
                   rec.entity.state_id.name,
                   rec.entity.zip,
                   rec.entity.country_id.name,
                   ]
            self.company_address = ', '.join(filter(bool, res))





    @api.onchange('account_no')
    def Account_details(self):
        for rec in self:
            rec.bank_title = rec.account_no.account_title
            rec.iban = rec.account_no.iban_no
            rec.swift_code = rec.account_no.account_swift_code

    @api.depends('name')
    def _compute_customer_address(self):
        for rec in self:
            res = [rec.name.street,
                   rec.name.street2,
                   rec.name.city,
                   rec.name.state_id.name,
                   rec.name.zip,
                   rec.name.country_id.name,
                   ]
            self.customer_address = ', '.join(filter(bool, res))


    @api.onchange('start_date', 'end_date', 'duration')
    def calculate_date(self):
        if self.start_date and self.end_date:
            d1 = datetime.strptime(str(self.start_date), '%Y-%m-%d')
            d2 = datetime.strptime(str(self.end_date), '%Y-%m-%d')
            days = (d2 - d1).days
            years, days = days // 365, days % 365
            months, days = days // 30, days % 30
            test = f"{years} Years {months} Months {days} Days"
            self.duration = str(test)


    @api.onchange('name')
    def customer_detail(self):
        for rec in self:
            rec.phone = rec.name.phone
            rec.email = rec.name.email

