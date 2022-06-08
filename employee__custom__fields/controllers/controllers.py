# -*- coding: utf-8 -*-
# from odoo import http


# class EmployeeCustomFields(http.Controller):
#     @http.route('/employee__custom__fields/employee__custom__fields', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/employee__custom__fields/employee__custom__fields/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('employee__custom__fields.listing', {
#             'root': '/employee__custom__fields/employee__custom__fields',
#             'objects': http.request.env['employee__custom__fields.employee__custom__fields'].search([]),
#         })

#     @http.route('/employee__custom__fields/employee__custom__fields/objects/<model("employee__custom__fields.employee__custom__fields"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('employee__custom__fields.object', {
#             'object': obj
#         })
