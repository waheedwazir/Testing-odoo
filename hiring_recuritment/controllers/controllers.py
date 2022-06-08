# -*- coding: utf-8 -*-
# from odoo import http


# class HiringRecuritment(http.Controller):
#     @http.route('/hiring_recuritment/hiring_recuritment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hiring_recuritment/hiring_recuritment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hiring_recuritment.listing', {
#             'root': '/hiring_recuritment/hiring_recuritment',
#             'objects': http.request.env['hiring_recuritment.hiring_recuritment'].search([]),
#         })

#     @http.route('/hiring_recuritment/hiring_recuritment/objects/<model("hiring_recuritment.hiring_recuritment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hiring_recuritment.object', {
#             'object': obj
#         })
