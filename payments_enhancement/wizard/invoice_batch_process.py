
import logging
import math
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
_logger = logging.getLogger(__name__)

class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.payment.register"

    deductions = fields.Many2many('deduction.payment.line', string="Deductions")
    journal_currency_id = fields.Many2one('res.currency', string="Journal's Currency", related='journal_id.currency_id',
        help='Utility field to express amount currency', readonly=True)
    total_due_amount = fields.Monetary(currency_field='journal_currency_id',readonly=True)
    amount_paid = fields.Monetary(currency_field='journal_currency_id')

    @api.onchange('deductions')
    def _onchange_deductions(self):
        if self.deductions:
            amount_paid = 0
            for deduction in self.deductions:
                if deduction.handling in ['FPWOD','FPWD']:
                    amount_paid += deduction.balance_amt
                elif deduction.handling in ['PPWOD', 'PPWD']:
                    amount_paid += deduction.receiving_amt
            self.amount_paid = amount_paid
            self.amount = amount_paid

    def _create_payments(self):
        payments = super(AccountRegisterPayments,self)._create_payments()
        for payment in payments:
            if self.deductions:
                payment.action_draft()
                amount = 0
                for deduction in self.deductions:
                    if deduction.handling in ['FPWOD','FPWD']:
                        amount += deduction.balance_amt
                    elif deduction.handling in ['PPWOD', 'PPWD']:
                        amount += deduction.receiving_amt
                # payment.amount = amount
                payment.write({
                    'amount': amount,
                    'deductions': [(0,0,{
                        'invoice_id': ded.invoice_id.id if ded.invoice_id else False,
                        'handling': ded.handling,
                        'balance_amt': ded.balance_amt,
                        'receiving_amt': ded.receiving_amt,
                        'account_id': ded.account_id.id if ded.account_id else False,
                        'currency_id': ded.currency_id.id if ded.currency_id else False,
                        'type': ded.type,
                        'taxes': ded.taxes.id if ded.taxes else False,
                        'amount_in_percent': ded.amount_in_percent,
                        'amount_payment': ded.amount_payment,
                    }) for ded in self.deductions]
                })
            res = payment.move_id.line_ids
            move_id = ''
            liquidity_line_id = '' # Bank,Cash, Credit Card journal item
            payment_move_receivable_lines = []
            invoice_move_receivable_lines = []
            for m_line in res:
                if m_line.account_id.user_type_id.type in ['receivable', 'payable']:
                    payment_move_receivable_lines.append(m_line.id)
                if m_line.account_id == m_line.move_id.journal_id.payment_debit_account_id:
                    move_id = m_line.move_id
                    liquidity_line_id = m_line
                elif m_line.account_id.user_type_id.type == 'liquidity': # Bank,Cash, Credit Card journal item
                    move_id = m_line.move_id
                    liquidity_line_id = m_line
            for deduction in payment.deductions.filtered(lambda ded:ded.handling in ['FPWD','PPWD']):        
                for m_line in deduction.invoice_id.mapped('line_ids'):
                    if m_line.account_id.user_type_id.type in ['receivable', 'payable']:
                        invoice_move_receivable_lines.append(m_line.id)
                if liquidity_line_id.credit > 0: #Bill or Customer Refund
                    deduction_vals = {
                            'partner_id':liquidity_line_id.partner_id.id,
                            'name':liquidity_line_id.name,
                            'payment_id':payment.id,
                            'credit':liquidity_line_id.currency_id.compute(deduction.amount_payment, self.company_id.currency_id),
                            'debit': 0,
                            'ref':liquidity_line_id.name,
                            'journal_id':payment.journal_id.id,
                            'move_id':deduction.invoice_id.id,
                            'currency_id': liquidity_line_id.currency_id.id,
                            'account_id':deduction.account_id.id}
                    move_id.write({
                        'line_ids':[(1,liquidity_line_id.id,{'credit':liquidity_line_id.credit - liquidity_line_id.currency_id.compute(deduction.amount_payment, self.company_id.currency_id)}),(0,0,deduction_vals)]
                    })
                else: # Customer Invoice or Bill Refund
                    deduction_vals = {
                            'partner_id':liquidity_line_id.partner_id.id,
                            'name':liquidity_line_id.name,
                            'payment_id':payment.id,
                            'credit':0,
                            'debit': liquidity_line_id.currency_id.compute(deduction.amount_payment, self.company_id.currency_id),
                            'ref':liquidity_line_id.name,
                            'journal_id':payment.journal_id.id,
                            'move_id':deduction.invoice_id.id,
                            'currency_id': liquidity_line_id.currency_id.id,
                            'account_id':deduction.account_id.id}
                    move_id.write({
                        'line_ids':[(0,0,deduction_vals),(1,liquidity_line_id.id,{'debit':liquidity_line_id.debit- liquidity_line_id.currency_id.compute(deduction.amount_payment, self.company_id.currency_id)})]
                    })
            payment.action_post()
            if payment_move_receivable_lines and invoice_move_receivable_lines:
                self.env['account.move.line'].browse(payment_move_receivable_lines+invoice_move_receivable_lines).filtered(lambda l:l.reconciled == False).reconcile()
        return payments


    @api.model
    def default_get(self, fields_list):
        rec = super(AccountRegisterPayments, self).default_get(fields_list)
        active_ids = self._context.get('active_ids')
        if not active_ids:
            return rec
        invoices = self.env['account.move'].browse(active_ids)
        ded_lines_dict = []
        if invoices !=None:
            amount_due = 0
            for inv in invoices:
                amount_due += inv.amount_residual
                ded_lines_dict.append((0, 0,{
                    'invoice_id': inv.id,
                    'handling':'FPWOD',
                    'balance_amt': inv.amount_residual,

                }))
        rec['total_due_amount'] = amount_due
        rec['amount_paid'] = amount_due
        rec['deductions'] = ded_lines_dict
        return rec