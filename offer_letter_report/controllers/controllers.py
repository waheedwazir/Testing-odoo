# -*- coding: utf-8 -*-
# from odoo import http


# class OfferLetterReport(http.Controller):
#     @http.route('/offer_letter_report/offer_letter_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/offer_letter_report/offer_letter_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('offer_letter_report.listing', {
#             'root': '/offer_letter_report/offer_letter_report',
#             'objects': http.request.env['offer_letter_report.offer_letter_report'].search([]),
#         })

#     @http.route('/offer_letter_report/offer_letter_report/objects/<model("offer_letter_report.offer_letter_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('offer_letter_report.object', {
#             'object': obj
#         })
