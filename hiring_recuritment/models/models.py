# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class HiringRecuritment(models.Model):
    _name = 'hiring.recuritment'
    _inherit = 'mail.thread'
    # _rec_name = 'department'

    name = fields.Char(string="New Employee Requisition", readonly=True, required=True, copy=False, default='New Employee Requisition')
    requestor = fields.Many2one('hr.employee', string='Requestor', required=1)
    sub_department = fields.Char(string='Department', readonly=1)
    department = fields.Char(string='Parent Department', readonly=1)
    disignation_of_employee = fields.Char(string='Designation',related='requestor.job_title' , store=True)
    location= fields.Many2one('location.status', string='Location')
    region = fields.Many2one('region.status', string='Region')
    directly_reporting = fields.Text(string='Directly Reporting To')
    state = fields.Selection([('new', 'New'), ('submit', 'Submit'), ('hod', 'HOD Approval'),('hr', 'HR Approval'), ('reject', 'Reject'),],default='new', track_visibility='always')
    hiring_recritment_line = fields.One2many('hiring_recuritment.line', 'recuritment_id')
    internal_job_posting = fields.Boolean(string='Internal Job Posting',)
    external_posting = fields.Boolean(string='External Sourcing')
    notes = fields.Html(string='Notes')
    position_type = fields.Selection(string='Position Type',
        selection=[('replacement_hiring', 'Replacement'),
                   ('new_hiring', 'New')],
        required=False, )
    job_detail_line = fields.One2many('job_detail.line', 'job_detail')
    request_date = fields.Date(string='Request Date', readonly=1 , default=datetime.today())

    @api.model
    def create(self, vals):
        if vals.get('name', 'New Employee Requisition') == 'New Employee Requisition':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'hiring.recuritment') or 'New Employee Requisition'
        result = super(HiringRecuritment, self).create(vals)
        return result

    @api.onchange('requestor')
    def onchange_requestor(self):
        for rec in self:
            self.sub_department = rec.requestor.department_id.name
            self.department = rec.requestor.department_id.parent_id.name
            # self.disignation_of_employee = rec.requestor.job_title



    def button_submit(self):
        for rec in self:
            rec.state = 'submit'

    def button_reject(self):
        for rec in self:
            rec.state = 'reject'

    def button_hod_approval(self):
        for rec in self:
            rec.state = 'hod'
    def button_hr_approval(self):
        for rec in self:
            rec.state = 'hr'
    def button_draft(self):
        for rec in self:
            rec.state = 'new'

class HiringRecuritmentLine(models.Model):
    _name = 'hiring_recuritment.line'

    recuritment_id = fields.Many2one('hiring.recuritment', string='Hiring Recruitment Line')
    employee_name= fields.Many2one('hr.resignation', string='Employee Name')
    report_to = fields.Char(string='Report To')
    state = fields.Selection(related='recuritment_id.state')
    department_id = fields.Char(string='Department')
    designation = fields.Char(string='Designation')
    date_of_resignation = fields.Date(string='Date Of Resignation')
    reason = fields.Selection([('resign', 'Resign'),
                               ('contract_end', 'Contract End'),
                               ('inv_separation', 'Involuntary Separation'),
                               ('transfer', 'Transfer')], string='Reason Of Leaving')

    @api.onchange('employee_name')
    def onchange_Hiring_Empl(self):
        for rec in self:
            self.department_id = rec.employee_name.department_id.name
            self.date_of_resignation = rec.employee_name.expected_revealing_date
            # self.designation = rec.employee_name.department_id.name


class JobDetails(models.Model):
    _name = 'job_detail.line'

    job_detail= fields.Many2one('hiring.recuritment', string='Job Details')
    state = fields.Selection(related='job_detail.state')
    hiring_department = fields.Many2one('hr.department', string='Hiring Department')
    new_position = fields.Many2one('hr.job', string='Job Position')
    pay = fields.Integer('Salary')
    job_type = fields.Selection([('fte', 'FTE'),
                                ('ftc', 'FTC'),
                                 ('temporary', 'Temporary'),
                                 ('intern', 'Intern')],
                                string='Employee Type')
    no_of_position = fields.Integer(string='No of Position')
    expected_start_date = fields.Date(string='Expected Start Date')
    location_id = fields.Many2one('location.status', string='Location')
