# -*- coding: utf-8 -*-
# from odoo import http


# class NdContractsReport(http.Controller):
#     @http.route('/nd_contracts_report/nd_contracts_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/nd_contracts_report/nd_contracts_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('nd_contracts_report.listing', {
#             'root': '/nd_contracts_report/nd_contracts_report',
#             'objects': http.request.env['nd_contracts_report.nd_contracts_report'].search([]),
#         })

#     @http.route('/nd_contracts_report/nd_contracts_report/objects/<model("nd_contracts_report.nd_contracts_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('nd_contracts_report.object', {
#             'object': obj
#         })
