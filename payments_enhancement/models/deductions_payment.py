# -*- coding: utf-8 -*-

from odoo import api, fields, models 
import logging
_logger = logging.getLogger(__name__)


class DeductionsPaymentLine(models.Model):
    _name = "deduction.payment.line"
    _rec_name = 'invoice_id'
    
    payment_id = fields.Many2one('account.payment', string="Payment")
    handling = fields.Selection([('FPWOD', 'Full Payment Without Deductions'),
                                 ('PPWOD', 'Partial Payment Without Deductions'),
                                 ('FPWD', 'Full Payment With Deductions'),
                                 ('PPWD', 'Partial Payment With Deductions'),
                                 ],
                                string="Payment Option",
                                copy=False, default='FPWOD', required=1)
    invoice_id = fields.Many2one('account.move', string="Customer Invoice")
    balance_amt = fields.Float("Taxable Amount")
    receiving_amt = fields.Float("Partial Amount")

    @api.onchange('payment_id.partner_id', 'invoice_id')
    def _get_bills(self):
        for item in self:
            data = []
            bills = self.env['account.move'].search([('partner_id', '=', item.payment_id.partner_id.id),
                                                    ('move_type', 'in', ('out_invoice', 'in_invoice'))])
            for bill in bills:
                data.append(bill.id)
            return {'domain': {'invoice_id': [('id', 'in', data)]}}



    # @api.onchange('taxes')
    # def _onchange_taxes(self):
    #     self.account_id = self.taxes.invoice_repartition_line_ids. \
    #         filtered(lambda tax: tax.repartition_type == 'tax' and tax.account_id).account_id
    #     self.amount_in_percent = self.taxes.amount
    #
    # @api.onchange('balance_amt', 'amount_in_percent')
    # def compute_amount_payment(self):
    #     if self.balance_amt and self.amount_in_percent:
    #         if self.handling in ['FPWD', 'FPWOD']:
    #             self.amount_payment = self.balance_amt * (self.amount_in_percent/100)
    #         else:
    #             self.amount_payment = self.receiving_amt * (self.amount_in_percent/100)

    @api.onchange("handling")
    def ChangeHandling(self):
        if self.handling in ('FPWOD', 'FPWD'):
            self.receiving_amt = 0

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        for record in self:
            if record.invoice_id:
                record.balance_amt = record.invoice_id.amount_residual
                 
    @api.onchange('receiving_amt')
    def ChangeReceiveingAmount(self):
        if self.handling == 'PPWOD' and self.payment_id:
            self.payment_id.amount = self.receiving_amt

    @api.model
    def default_get(self, fields_list):
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        rec = {}
        if active_ids != None:
            rec = self.env['account.move'].search([('id', '=', active_ids[0])])
            invoice_id = active_ids[0]
            rec = {'invoice_id': rec.id, 'balance_amt': rec.amount_residual, 'handling': 'FPWOD'}
        return rec


class DeductionsTaxLine(models.Model):
    _name = "deduction.tax.line"

    payment_id = fields.Many2one('account.payment', string="Payment")
    invoice_id = fields.Many2one('account.move', string="Customer Invoice")
    amount = fields.Float("Amount")
    payment_difference = fields.Float(string='Difference Amount', readonly=True)
    account_id = fields.Many2one('account.account', string="Account Ledger", domain=[('deprecated', '=', False)], copy=False)
    description = fields.Char('Description')
    amount_in_percent = fields.Float(string='Deduction(%)', digits=(16, 2))
    amount_payment = fields.Monetary(string='Deducted Amount')
    currency_id = fields.Many2one('res.currency', string='Currency', related='invoice_id.currency_id')
    type = fields.Selection([('sales_WHT', 'Sales Tax Withheld'),
                             ('income_WHT', 'Income Tax Withheld'),
                             ('other', 'Other')], string='Type')
    taxes = fields.Many2one('account.tax', string='Taxes')

    @api.onchange('payment_id', 'invoice_id')
    def _get_bills(self):
        for item in self.payment_id:
            data = []
            for line in item.deductions:
                if line.handling in ('FPWD', 'PPWD'):
                    bill = line.invoice_id.id
                    data.append(bill)
                    if line.handling == 'FPWD' and self.invoice_id.id == line.invoice_id.id:
                        self.amount = line.balance_amt
                    elif line.handling == 'PPWD' and self.invoice_id.id == line.invoice_id.id:
                        self.amount = line.receiving_amt
            return {'domain': {'invoice_id': [('id', 'in', data)]}}

    @api.onchange('taxes', 'type')
    def get_type(self):
        for item in self:
            data = []
            tax = self.env['account.tax'].search([('sales_income_wht', '=', item.type)])
            for line in tax:
                data.append(line.id)
            return {'domain': {'taxes': [('id', 'in', data)]}}


    @api.onchange('taxes')
    def _onchange_taxes(self):
        self.account_id = self.taxes.invoice_repartition_line_ids. \
            filtered(lambda tax: tax.repartition_type == 'tax' and tax.account_id).account_id
        self.amount_in_percent = self.taxes.amount

    @api.onchange('amount', 'amount_in_percent')
    def compute_amount_payment(self):
        if self.amount and self.amount_in_percent:
            self.amount_payment = self.amount * (self.amount_in_percent / 100)
