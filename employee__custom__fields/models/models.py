# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime


class EmployeeCustomFields(models.Model):
    _inherit = 'hr.employee'

    current_address = fields.Char('Current Address')
    permanent_address = fields.Char('Permanent Address')
    eobi_no = fields.Char('EOBI No.')
    # hobbies = fields.Many2many('hr.hobbies','hr_hobbies_id',string='Hobbies')
    state_id = fields.Selection(
        string='States',
        selection=[('submit_for_hr_review', 'Submit for HR Review'),
                   ('reviewed', 'reviewed'),
                   ('done', 'Resend to Employee'),],
        required=False, )
    bool = fields.Boolean('')
    bool_review = fields.Boolean('')


    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    state = fields.Char()
    zip = fields.Char()
    p_street = fields.Char()
    p_street2 = fields.Char()
    p_city = fields.Char()
    p_state = fields.Char()
    p_zip = fields.Char()
    from_date = fields.Date(string="Joining date")
    final_date = fields.Date(string="End date")
    total_days = fields.Char(string="Total Experience")

    @api.onchange('from_date', 'final_date', 'total_days')
    def calculate_date(self):
        if self.from_date and self.final_date:
            d1 = datetime.strptime(str(self.from_date), '%Y-%m-%d')
            d2 = datetime.strptime(str(self.final_date), '%Y-%m-%d')
            days = (d2 - d1).days
            years, days = days // 365, days % 365
            months, days = days // 30, days % 30
            test = f"{years} Years {months} Months {days} Days"
            self.total_days = str(test)

    # def submit(self):
    #     self.send_email()



    def send_email(self):
        self.state_id = 'submit_for_hr_review'
        temp_id = self.env.ref('employee__custom__fields.email_template_id').id
        template= self.env['mail.template'].browse(temp_id)
        template.send_mail(self.id, force_send=True)


    def reviewed(self):
        self.state_id = 'reviewed'
        self.bool_review = True

    def resend_to_employee(self):
        self.state_id = 'done'
        self.bool = True


class ResumeCustomField(models.Model):
    _inherit = 'hr.resume.line'

    total_exp = fields.Char(string="Total Experience")

    @api.onchange('date_start', 'date_end', 'total_exp')
    def calculate_date(self):
        if self.date_start and self.date_end:
            d1 = datetime.strptime(str(self.date_start), '%Y-%m-%d')
            d2 = datetime.strptime(str(self.date_end), '%Y-%m-%d')
            days = (d2 - d1).days
            years, days = days // 365, days % 365
            months, days = days // 30, days % 30
            test = f"{years} Years {months} Months {days} Days"
            self.total_exp = str(test)


class HrEMployee(models.Model):
    _inherit = 'hr.employee'

    total_exp = fields.Char(
        'Total Exp', compute='_cal_total_exp')
    company_exp = fields.Char(
        'Total Exp', compute='_cal_company_exp')
    relavant_exp = fields.Char(
        'Total Exp', compute='_cal_relavant_exp')

    def cal_exp_str(self, months, years):
        exp_str = ''
        for rec in self:
            new_month = 0
            if months > 12:
                new_year = months / 12
                years += new_year
                new_month = (months - 12 * (months // 12))
                months = new_month
            exp_str = (str(round(years)) + ' ' + 'Year(s)' + ' ' +
                       str(months) + ' ' + 'Month(s)' + ' ')
            return exp_str

    @api.depends('resume_line_ids.date_start',
                 'resume_line_ids.date_end')
    def _cal_total_exp(self):
        for employee in self:
            months = 0
            years = 0
            total_exp_str = ''
            for resume_line in employee.resume_line_ids:
                exp_rec = resume_line.filtered(
                    lambda r: resume_line.line_type_id.name == 'Experience')
                months += exp_rec.months
                years += exp_rec.years
            total_exp_str = self.cal_exp_str(months, years)
            employee.total_exp = total_exp_str

    @api.depends('resume_line_ids.date_start',
                 'resume_line_ids.date_end')
    def _cal_company_exp(self):
        for employee in self:
            months = 0
            years = 0
            total_company_str = ''
            for resume_line in employee.resume_line_ids:
                exp_rec = resume_line.filtered(
                    lambda r: resume_line.line_type_id.name == 'Experience'
                              and resume_line.current_compnay)
                months += exp_rec.months
                years += exp_rec.years
            total_company_str = self.cal_exp_str(months, years)
            employee.company_exp = total_company_str

    @api.depends('resume_line_ids.date_start',
                 'resume_line_ids.date_end',
                 'resume_line_ids.line_type_id')
    def _cal_relavant_exp(self):
        for employee in self:
            months = 0
            years = 0
            for resume_line in employee.resume_line_ids:
                exp_rec = resume_line.filtered(
                    lambda r: resume_line.line_type_id.name == 'Experience'
                              and resume_line.relavent_experience)
                months += exp_rec.months
                years += exp_rec.years
            employee.relavant_exp = self.cal_exp_str(months, years)

    @api.depends('resume_line_ids.date_start',
                 'resume_line_ids.date_end',
                 'resume_line_ids.current_compnay',
                 'resume_line_ids.line_type_id',
                 'resume_line_ids.relavent_experience')
    def _cal_total_experience(self):
        for employee in self:
            total_exp = sum([
                resume_line.experience for resume_line in
                employee.resume_line_ids if
                resume_line.line_type_id.name == 'Experience'])
            relavant_exp = sum([
                resume_line.experience for resume_line in
                employee.resume_line_ids if
                resume_line.line_type_id.name == 'Experience'
                and resume_line.relavent_experience])
            company_exp = sum([
                resume_line.experience for resume_line in
                employee.resume_line_ids if
                resume_line.line_type_id.name == 'Experience'
                and resume_line.current_compnay])
            employee.total_experience = total_exp
            employee.relavant_experience = relavant_exp
            employee.company_experience = company_exp


class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'

    experience = fields.Float('Experience', compute='_calc_experience')
    experience_str = fields.Char('Experience', compute='_calc_experience')
    current_compnay = fields.Boolean('Current Company', copy=False)
    relavent_experience = fields.Boolean(copy=False)
    attachment = fields.Binary(string='Attachment', copy=False)
    file_name = fields.Char('File name', copy=False)
    company_name = fields.Char('Company name', copy=False)
    months = fields.Integer()
    years = fields.Integer()

    @api.depends('date_start', 'date_end', 'line_type_id')
    def _calc_experience(self):
        for resume_line in self:
            exp_rec = resume_line.filtered(
                lambda r: resume_line.line_type_id.name == 'Experience')
            if exp_rec.date_end:
                diff = relativedelta(
                    exp_rec.date_end, exp_rec.date_start)
                diff_months = relativedelta(
                    exp_rec.date_end, exp_rec.date_start).years * 12 + \
                              relativedelta(
                                  exp_rec.date_end, exp_rec.date_start).months
            else:
                diff = relativedelta(
                    datetime.today().date(),
                    exp_rec.date_start)
                diff_months = relativedelta(
                    datetime.today().date(),
                    exp_rec.date_start).years * 12 + relativedelta(
                    datetime.today().date(), exp_rec.date_start).months
            diff_months = diff.months
            years = diff.years
            resume_line.experience_str = (str(years) + ' ' + 'Year(s)' + ' ' +
                                          str(diff_months) + ' ' + 'Month(s)' + ' ')
            resume_line.experience = diff_months
            resume_line.years = diff.years
            resume_line.months = diff.months




