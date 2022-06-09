# -*- coding: utf-8 -*-

from odoo import models, fields, api
import math

class TaxLocalizationLine(models.Model):
    _name = 'tax.slab.line'
    _description = 'Slab Lines for Taxes'

    name = fields.Char(string='Slab', compute="_compute_name")
    from_value = fields.Float(string='From', required=True)
    to_value = fields.Float(string='To', required=True)
    tax_value = fields.Float(string='Tax(%)', required=True)
    additional_value = fields.Float(string='Previous Slabs Tax')
    # dividing_factor = fields.Float(string='Dividing Factor')
    tax_id = fields.Many2one('account.tax', string='Tax')

    @api.depends('from_value', 'to_value')
    def _compute_name(self):
        for record in self:
            name = ''
            name += str(record.from_value)
            name += "--"
            name += str(record.to_value)
            record.name = name

class AccountTax(models.Model):
    _inherit = 'account.tax'

    is_slab_tax = fields.Boolean(string='Slab Tax', default=False)
    amount_type = fields.Selection(string="Tax Computation",
        selection=[
            ('group', 'Group of Taxes'), 
            ('fixed', 'Fixed'), 
            ('percent', 'Percentage of Price'), 
            ('division', 'Percentage of Price Tax Included'),
            ('slabs', 'Slabs')
            ])
    territory = fields.Selection([('federal', 'Federal'), ('punjab', 'Punjab'), ('sindh', 'Sindh'),
                                ('kpk-e', 'KPK corporate entities'), ('kpk-o', 'KPK others'),
                                ('balouchistan', 'Balouchistan')])
    slab_line_ids = fields.One2many('tax.slab.line', 'tax_id', string='Tax Slab Lines')
    
    
    @api.onchange('amount_type')
    def _onchange_amount_type(self):
        for record in self:
            if record.amount_type == 'slabs':
                record.type_tax_use = 'none'