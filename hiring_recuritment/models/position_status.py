from odoo import models, fields, api


class PositionStatus(models.Model):
    _name = 'position.status'
    _inherit = 'mail.thread'
    _rec_name = 'position_status'


    position_status = fields.Char(string='Position Status', required=1)


class Location(models.Model):
    _name = 'location.status'
    _inherit = 'mail.thread'
    _rec_name = 'location'

    location = fields.Char(string='location', required=1)

class Region(models.Model):
    _name = 'region.status'
    _inherit = 'mail.thread'
    _rec_name = 'region'

    region = fields.Char(string='Region', required=1)

class HrHoddies(models.Model):
    _name = 'hr.hobbies'

    hobbies = fields.Char('Hobbies', required=1)



