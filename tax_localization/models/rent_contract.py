# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__) 

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'product.template'
    
    rent_ok = fields.Boolean('Rent', default=False)

class AccountMove(models.Model):
    _inherit = 'account.move'

    rent_contract_id = fields.Many2one('rent.contract', string='Contract')
    
    @api.onchange('rent_contract_id')
    def _onchange_rent_contract_id(self):
        if self.rent_contract_id:
            product_id = self.rent_contract_id.product_id
            new_lines = self.env['account.move.line']
            rent_line = new_lines.new({
                    'name': 'Service Contract Line', 
                    'price_unit': self.rent_contract_id.rent_per_interval,
                    'quantity': self.rent_contract_id.payment_period,
                    'product_id': product_id.id, 
                    'product_uom_id': product_id.uom_id.id if product_id.uom_id else False,
                    'tax_ids': [(6,0,product_id.taxes_id.ids)] if product_id.taxes_id else False,
                    'move_id': self.id,
                    'account_id': product_id.property_account_expense_id.id if product_id.property_account_expense_id else False,
                    'price_subtotal': self.rent_contract_id.rent_per_interval,
            })
            rent_line.recompute_tax_line = True
            self._recompute_dynamic_lines()
            rent_line.account_id = rent_line._get_computed_account()
            rent_line._onchange_price_subtotal()
            new_lines += rent_line
            new_lines._onchange_mark_recompute_taxes()
            self._onchange_currency()


            
class RentContract(models.Model):
    _name = 'rent.contract'
    _description = 'Rent Contract'

    name = fields.Char(string='Number',default="New")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('close', 'Closed')
    ], string='Status', default='draft')
    rent_per_interval = fields.Float(string='Amount Per Month')
    number_of_interval = fields.Integer(string='No. of Months')
    payment_period = fields.Integer(string='Payment Period')
    total_rent = fields.Float(string='Total Amount', compute="compute_total_rent")
    tax_id = fields.Many2one('account.tax', domain="[('company_id', '=', company_id)]", string='Tax')
    product_id = fields.Many2one('product.product',
                                 domain="[('rent_ok', '=', True),'|',('company_id', '=', False),"
                                        "('company_id', '=', company_id)]", string='Service', required=True)
    total_tax = fields.Float(string='Total Tax', compute="compute_taxes")
    tax_per_interval = fields.Float(string='Tax Per Month', compute="compute_taxes")
    gross_rent_paid = fields.Float(string='Gross Amount Paid')
    tax_deducted = fields.Float(string='Total Tax Paid')
    remaining_gross_rent = fields.Float(string='Remaining Gross Amount', compute="compute_remaining")
    remaining_tax = fields.Float(string='Remaining Tax', compute="compute_remaining")
    partner_id = fields.Many2one('res.partner', domain="[('company_id', '=', company_id)]", string='Partner')
    invoice_ids = fields.One2many('account.move', 'rent_contract_id', string='Invoices')
    invoices_count = fields.Integer(string='Invoices', compute="compute_invoices_count")
    notes = fields.Html(string='Notes')
    company_id = fields.Many2one('res.company', string='Company', required=True, index=True,
                                 default=lambda self: self.env.company)

    # @api.depends('invoice_ids')
    # def compute_paid_amounts(self):
    #     for record in self:
    #         if record.invoice_ids:
    #             query = """
    #                 SELECT payment_id
    #                 FROM account_move_line AS aip
    #                 WHERE aip.move_id IN %s
    #             """
    #             self.env.cr.execute(query, (tuple(record.invoice_ids.ids),))
    #             payment_ids = [res['payment_id'] for res in self.env.cr.dictfetchall()]
    #             payments = self.env['account.payment'].browse(payment_ids) if payment_ids else []
    #             gross_rent_paid = 0
    #             tax_deducted = 0
    #             for payment in payments:
    #                 if payment.state not in ['draft', 'cancelled']:
    #                     for deduction in payment.deductions:
    #                         for line in deduction.writeoff_account_id_.writeoff_line:
    #                             if line.taxes == record.tax_id:
    #                                 tax_deducted += line.amount_payment
    #                                 gross_rent_paid -= line.amount_payment
    #                     # _logger.info("Payment: "+payment.name+"Amount Paid: "+str(payment.amount_paid)+"Net Amount: "+str(payment.amount))
    #                     gross_rent_paid += payment.amount
    #                     # tax_deducted += (payment.amount-payment.amount_paid)
    #             record.gross_rent_paid = gross_rent_paid
    #             record.tax_deducted = tax_deducted
    #         else:
    #             record.gross_rent_paid = 0
    #             record.tax_deducted = 0

    @api.depends('gross_rent_paid', 'total_rent', 'tax_deducted', 'total_tax')
    def compute_remaining(self):
        for record in self:
            record.remaining_gross_rent = record.total_rent - record.gross_rent_paid
            record.remaining_tax = record.total_tax - record.tax_deducted

    @api.depends('tax_id', 'number_of_interval', 'rent_per_interval')
    def compute_taxes(self):
        for record in self:
            if record.total_rent and record.tax_id:
                for line in record.tax_id.slab_line_ids:
                        if record.rent_per_interval >= line.from_value and record.rent_per_interval <= line.to_value:
                            percent_tax = 0
                            additional_tax = line.additional_value
                            if line.tax_value > 0:
                                percent_tax = record.total_rent * (line.tax_value / 100)
                            record.total_tax = additional_tax + percent_tax
                record.tax_per_interval = record.total_tax / record.number_of_interval
            else:
                record.total_tax = 0
                record.tax_per_interval = 0
            # record.compute_paid_amounts()

    @api.depends('number_of_interval', 'rent_per_interval')
    def compute_total_rent(self):
        for record in self:
            record.total_rent = record.number_of_interval * record.rent_per_interval
    
    def compute_invoices_count(self):
        for record in self:
            record.invoices_count = len(record.invoice_ids) if record.invoice_ids else 0

    def open_invoices(self):
        return {
            'name': _('Vendor Contract Bills'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'views': [(self.env.ref('account.view_move_tree').id, 'tree'), (self.env.ref('account.view_move_form').id, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.invoice_ids])],
            'context': {'create': False},
        }

    def action_draft(self):
        self.write({'state': 'draft'})
    
    def action_open(self):
        self.write({'state': 'open'})
        if self.name == _('New'):
            self.name = self.env['ir.sequence'].next_by_code('rent.contract') or _('New')
    
    def action_close(self):
        self.write({'state': 'close'})

class DeductionsPaymentLineSlabs(models.Model):
    _inherit = "deduction.payment.line"

    slab_tax = fields.Float(string='Slab Tax')


    @api.onchange('taxes')
    def _onchange_taxes(self):
        self.account_id = self.taxes.invoice_repartition_line_ids. \
            filtered(lambda tax: tax.repartition_type == 'tax' and tax.account_id).account_id
        self.amount_in_percent = self.taxes.amount
        if self.taxes and self.taxes.amount_type == 'slabs':
            self.amount_payment = self.slab_tax
            self.amount_in_percent = 0



class AccountPaymentRent(models.Model):
    _inherit = "account.payment"

    # @api.model
    # def default_get(self, fields_list):
    #     rec = super(AccountPaymentRent, self).default_get(fields_list)
    #     active_ids = self._context.get('active_ids')
    #     if not active_ids:
    #         return rec
    #     ded_lines_dict = rec['deductions']
    #     ded_new_lines = []
    #     for ded in ded_lines_dict:
    #         inv = self.env['account.move'].browse(ded[2]['invoice_id'])
    #         if inv.rent_contract_id:
    #             ded[2]['handling'] = 'FPWD'
    #             ded[2]['balance_amt'] = inv.rent_contract_id.rent_per_interval * inv.invoice_line_ids[0].quantity
    #             ded[2]['slab_tax'] = inv.rent_contract_id.tax_per_interval * inv.invoice_line_ids[0].quantity
    #         ded_new_lines.append(ded)
    #     rec['deductions'] = ded_lines_dict
    #     return rec
    #

    def action_post(self):
        rec = True
        for record in self:
            rec = super(AccountPaymentRent, record).action_post()
            if record.deductions:
                rent = self.env['rent.contract'].search([('id', '=', self.deductions.invoice_id.id)])
                if rent:
                    print('nadir')
