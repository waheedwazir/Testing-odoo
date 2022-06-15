# -*- coding: utf-8 -*-
# from odoo import http


# class CustomerContract(http.Controller):
#     @http.route('/customer_contract/customer_contract', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer_contract/customer_contract/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer_contract.listing', {
#             'root': '/customer_contract/customer_contract',
#             'objects': http.request.env['customer_contract.customer_contract'].search([]),
#         })

#     @http.route('/customer_contract/customer_contract/objects/<model("customer_contract.customer_contract"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer_contract.object', {
#             'object': obj
#         })
