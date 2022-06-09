# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError

from odoo import api, fields, models, _


class AccountPayment(models.Model):
    _inherit = "account.payment"

    deductions = fields.One2many('deduction.payment.line', 'payment_id')
    taxes = fields.One2many('deduction.tax.line', 'payment_id')
    pay_ref = fields.Char('Ref', store=True)
    journal_currency_id = fields.Many2one('res.currency', string="Journal's Currency",
                                          related='journal_id.currency_id',
                                          help='Utility field to express amount currency', readonly=True)
    amount_paid = fields.Monetary(string='Gross Amount', compute="_onchange_deductions", store=True)
    total_deduction = fields.Float('Total Deduction', compute="compute_deduction", store=True)

    @api.depends('taxes', 'taxes.amount', 'taxes.amount_payment')
    def compute_deduction(self):
        for rec in self:
            rec.total_deduction = sum([(p.amount_payment) for p in rec.taxes])


    # @api.depends('move_id.line_ids')
    # def _compute_amount_paid(self):
    #     liquidity_lines = self.move_id.line_ids.filtered(lambda line:line.account_id.user_type_id.type == 'liquidity')
    #     amount_paid = 0
    #     for line in liquidity_lines:
    #         amount_paid += line.debit
    #         amount_paid += line.credit
    #     self.amount_paid = amount_paid
    
    @api.onchange('deductions', 'taxes')
    def _onchange_deductions(self):
        if self.deductions:
            amount_paid = 0
            for deduction in self.deductions:
                if deduction.handling in ['FPWOD', 'FPWD']:
                    amount_paid += deduction.balance_amt
                elif deduction.handling in ['PPWOD', 'PPWD']:
                    amount_paid += deduction.receiving_amt
            self.amount = amount_paid
            self.amount_paid = amount_paid - self.total_deduction

    def action_post(self):
        rec = True
        for record in self:
            rec = super(AccountPayment, record).action_post()
            record.state = 'draft'
            res = record.move_id.line_ids
            if record.deductions and record.taxes:
                invoice_id = False
                for line in res:
                    invoice_id = line.move_id.id
                    for deduction in record.taxes:
                        for dedline in deduction:
                            line.reconciled = False
                            if line.credit > 0: # Vendor Bills or Credit notes
                                deduction_vals = {
                                        'partner_id': record.partner_id.id,
                                        'name': record.name,
                                        'payment_id': record.id,
                                        'credit': line.currency_id.compute(dedline.amount_payment, dedline.currency_id),
                                        'debit': 0,
                                        'ref': record.name,
                                        'journal_id': record.journal_id.id,
                                        'move_id': invoice_id,
                                        'account_id': dedline.account_id.id}
                                line.move_id.write({
                                    'line_ids': [(1, line.id, {
                                        'credit': line.credit - line.currency_id.compute(dedline.amount_payment, dedline.currency_id)}), (0, 0, deduction_vals)]
                                })
                            # else: # Customer Invoice or Bill Refund
                            #     deduction_vals = {
                            #             'partner_id': record.partner_id.id,
                            #             'name': record.name,
                            #             'payment_id': record.id,
                            #             'credit': 0,
                            #             'debit': line.currency_id.compute(dedline.amount_payment, self.company_id.currency_id),
                            #             'ref': record.name,
                            #             'journal_id': record.journal_id.id,
                            #             'move_id': invoice_id,
                            #             'account_id': dedline.account_id.id}
                            #     line.move_id.write({
                            #         'line_ids': [(0, 0, deduction_vals), (1, line.id, {
                            #             'debit': line.debit - line.currency_id.compute(dedline.amount_payment, self.company_id.currency_id)})]
                            #     })
                            line.reconciled = True
                record.state = 'posted'
        return rec

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                # if len(liquidity_lines) != 1 or len(counterpart_lines) != 1:
                #     raise UserError(_(
                #         "The journal entry %s reached an invalid state relative to its payment.\n"
                #         "To be consistent, the journal entry must always contains:\n"
                #         "- one journal item involving the outstanding payment/receipts account.\n"
                #         "- one journal item involving a receivable/payable account.\n"
                #         "- optional journal items, all sharing the same account.\n\n"
                #     ) % move.display_name)

                # if writeoff_lines and len(writeoff_lines.account_id) != 1:
                #     raise UserError(_(
                #         "The journal entry %s reached an invalid state relative to its payment.\n"
                #         "To be consistent, all the write-off journal items must share the same account."
                #     ) % move.display_name)

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal items must share the same currency."
                    ) % move.display_name)

                if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal items must share the same partner."
                    ) % move.display_name)

                if counterpart_lines.account_id.user_type_id.type == 'receivable':
                    partner_type = 'customer'
                else:
                    partner_type = 'supplier'

                liquidity_amount = liquidity_lines.amount_currency

                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount),
                    'payment_type': 'inbound' if liquidity_amount > 0.0 else 'outbound',
                    'partner_type': partner_type,
                    'currency_id': liquidity_lines.currency_id.id,
                    'destination_account_id': counterpart_lines.account_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))


        
class InheritPartner(models.Model):
    _inherit = 'res.partner'

    over_credit = fields.Char('Over credit')