from odoo import fields,models,api

class BankAccount(models.Model):
    _name = 'bank.account'
    _inherit = 'mail.thread'
    _rec_name = 'account'

    account = fields.Char('Account No.',required=True ,tracking=True,)
    account_title = fields.Char(string='Account Title')
    iban_no = fields.Char(string='IBAN')
    account_swift_code = fields.Char(string='Swift Code')

