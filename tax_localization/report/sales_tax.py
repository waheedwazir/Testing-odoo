# -*- coding: utf-8 -*-

from odoo import models, fields, api
from collections import Counter
from odoo.tools import date_utils
import io
import json
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ExportSalesTax(models.TransientModel):
    _name = 'export.sales.tax'

    date_to = fields.Date('Date To')
    date_from = fields.Date('Date From')

    def export(self):
        account_move = self.env['account.move']
        invoices = account_move.search([('create_date', '>=', self.date_from), ('create_date', '<=', self.date_to), ('name','ilike','INV'), ('name','not ilike','RINV')])
        data1 = []
        data2 = []
        # for item in invoices:
        #     for i in item.invoice_line_ids:
        #         data2.append({
        #             'invoice_name':item.name,
        #             'sale_order': item.invoice_origin or '',
        #             'date': item.date,
        #             'product_name': i.product_id.name or '',
        #             'partner_id':item.partner_id.name or '',
        #             'partner_name':item.partner_id.name or '',
        #             'fiscal_position':item.fiscal_position_id.name or '',
        #             'created_by':item.create_uid.name or '',
        #             'sale_person':item.invoice_user_id.name or '',
        #             'product_internal_reference':i.product_id.default_code or '',
        #             'product_id':i.product_id.main_id.id or '',
        #             'parent_category':i.product_id.parent_categ_id.name or '',
        #             'product_category':i.product_id.categ_id.name or '',
        #             'brand':i.product_id.brand_id.name or '',
        #             'type':'Storable Product',#i.product_id.type or '',
        #             # 'price':i.subtotal,
        #             'quantity': i.quantity or '',
        #             'maker': i.product_id.maker_id.name or '',
        #             'mfr': i.product_id.manufacturer_id.name or '',
        #             'model': i.product_id.model_id.name or '',
        #             'priceunit': i.price_unit or 0,
        #             'cost': i.product_id.standard_price or 0,
        #             'discount': i.discount or 0,
        #             'total': i.price_subtotal or 0,
        #             'amount_due': item.amount_residual or 0,
        #         })

        return {
            'type': 'ir_actions_xlsx_download',
            'data': {'model': 'export.invoices',
                     'options': json.dumps(data2, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Sales Comprehensive Report',
                     }
                }
    def get_xlsx_report(self, data, response):
        output = io.BytesIO()

        list4 = ['Tax Period', 'NTN', 'Name of Buyer', 'Invoice Number', 'Invoice Date', 'Value of supplies/ services ', 'Sales Tax Rate %',
                 'Sales tax ', 'Territory']

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        sheet = workbook.add_worksheet('General Sales Tax')
        # sheet1 = workbook.set_column()
        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        col_head = workbook.add_format({'align': 'center', 'font_size': '11px', 'bold': True, 'border': 2})
        txt = workbook.add_format({'align': 'center', 'font_size': '10px'})
        txt1 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})

        col = 0
        for line in list4:
            sheet.write(0, col, line, txt1)
            col = col + 1

        # row = 2
        #
        # col = 0
        # for j in data:
        #
        #     sheet.write(row, col, j['invoice_name'], txt)
        #     sheet.write(row, col+1, j['sale_order'], txt)
        #     sheet.write(row, col+2, j['date'], txt)
        #     sheet.write(row, col+3, j['product_name'], txt)
        #     sheet.write(row, col+4, j['product_internal_reference'], txt)
        #     sheet.write(row, col+5, j['product_id'], txt)
        #     sheet.write(row, col+6, j['type'], txt)
        #     sheet.write(row, col+7, j['parent_category'], txt)
        #     sheet.write(row, col+8, j['product_category'], txt)
        #     sheet.write(row, col+9, j['brand'], txt)
        #     sheet.write(row, col+10, j['sale_person'], txt)
        #     sheet.write(row, col+11, j['created_by'], txt)
        #     sheet.write(row, col+12, j['partner_name'], txt)
        #     sheet.write(row, col+13, j['fiscal_position'], txt)
        #     sheet.write(row, col+14, j['maker'], txt)
        #     sheet.write(row, col+15, j['mfr'], txt)
        #     sheet.write(row, col+16, j['model'], txt)
        #     sheet.write(row, col+17, j['quantity'], txt)
        #     sheet.write(row, col+18, j['priceunit'], txt)
        #     sheet.write(row, col+19, j['cost'], txt)
        #     sheet.write(row, col+20, j['discount'], txt)
        #     margin = (j['priceunit']-j['cost']-j['discount'])*j['quantity']
        #     if margin == '':
        #         sheet.write(row, col+21, '', txt)
        #     else:
        #         sheet.write(row, col+21, "{:.2f}".format(float((j['priceunit']-j['cost']-j['discount'])*j['quantity'])), txt)
        #     gp = (j['priceunit']-j['cost'])*j['quantity']
        #     if gp == '':
        #         sheet.write(row, col+22, '', txt)
        #     else:
        #         sheet.write(row, col+22, "{:.2f}".format(float((j['priceunit']-j['cost'])*j['quantity'])), txt)
        #     sheet.write(row, col+23, j['total'], txt)
        #     # sheet.write(row, col+24, j['amount_due'], txt)
        #
        #     row = row+1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()