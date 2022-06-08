from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
import calendar

class tax_slab(models.Model):
    _name = 'tax.slab'

    @api.onchange('date_from','date_to','company_id')
    def _get_date(self):
        print('tax slab')
        if self.date_from and self.date_to and self.company_id:
            self.name = "Salary Tax Slab of "+self.company_id.name+" for the period " + str(self.date_from)+'-'+str(self.date_to)

    name = fields.Char(string="Name", compute=_get_date, store=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, string='Company')
    fiscal_year = fields.Many2one('account.fiscal.year', string="Fiscal Year")
    date_from = fields.Date()
    date_to = fields.Date()
    tax_slab_detail = fields.One2many('tax.slab.line', 'tax_slab_id', 'Tax Slabs')
    state = fields.Selection([('Draft', 'Draft'), ('Active', 'Active'), ('Obselete', 'Archived')], default='Draft')
    user_id = fields.Many2one('res.users', 'User')
    confirm_date = fields.Date('Confirm Date')
    obselete_date = fields.Date('Obsolete Date')

    def activate_slab(self):
        self.write({'user_id': self.env.user.id,
                    'confirm_date': fields.Datetime.now(),
                    'state': 'Active'})

    def obselete_slab(self):
        self.write({'user_id': self.env.user.id,
                    'obselete_date': fields.Datetime.now(),
                    'state': 'Obselete'})

    def unlink(self):
        for each in self:
            if each.state != 'Draft':
                raise ValidationError('Invalid Action! You cannot delete this record.')
        return super(tax_slab, self).unlink()

    @api.constrains('tax_slab_detail')
    def _check_slab_overlaping(self):
        slab_details = self.tax_slab_detail
        slab_pool = self.env['tax.slab.line']
        if slab_details:
            for slab in slab_details:
                if slab.upper_limit <= slab.lower_limit and not slab.no_upper_limit:
                    raise ValidationError('Tax slab upper limit must be greater than lower limit')
                overlaping_lower_limit = slab_pool.search(
                    [('lower_limit', '<=', slab.lower_limit), ('upper_limit', '>=', slab.lower_limit),
                     ('tax_slab_id', '=', self.id)])
                if len(overlaping_lower_limit) > 1:
                    raise ValidationError(_('Tax slab Lower limit (%s) can not be overlapped') % (str(slab.lower_limit)))
                overlaping_upper_limit = slab_pool.search(
                    [('lower_limit', '<=', slab.upper_limit), ('upper_limit', '>=', slab.upper_limit),
                     ('tax_slab_id', '=', self.id)])
                if len(overlaping_upper_limit) > 1:
                    raise ValidationError(_('The slab Upper limit (%s) can not be overlapped') % (str(slab.upper_limit)))

    @api.constrains('state')
    def check_tax_slab(self):
        if self:
            result = self.env['tax.slab'].search([('state', '=', 'Active'), ('id', '!=', self.id),('company_id','=',self.company_id.id)])
            if result:
                raise ValidationError('Tax chart in active state')
        else:
            result = self.env['tax.slab'].search([('state', '=', 'active')])
            if len(result) > 1:
                raise ValidationError('Tax chart already in active state')


class pk_pr_tax_slab_line(models.Model):
    _name = 'tax.slab.line'

    lower_limit = fields.Integer('Lower Limit', required=True)
    upper_limit = fields.Integer('Upper Limit', required=True)
    tax_rate = fields.Float('Tax Rate(%)', required=True)
    fix_amount = fields.Integer('Fixed Amount to be added', required=True)
    tax_slab_id = fields.Many2one('tax.slab', 'Tax Slab ID', ondelete='cascade')
    no_upper_limit=fields.Boolean(string='No Upper limit')

    @api.onchange('no_upper_limit')
    def CheckUpperLimit(self):
        self.upper_limit=0

class InheitHRContract(models.Model):
    _inherit = 'hr.contract'

    def diff_month(self, d1, d2):
        return (d1.year - d2.year)*12 + d1.month - d2.month

    def _cal_date(self, date_from, date_to, joining_date):
        month = date_from.month
        year = date_from.year
        work_days = 0
        work_days_from_joining = date_to-joining_date
        work_days_from_payslip = date_to-date_from
        if work_days_from_joining.days < work_days_from_payslip.days:
            work_days = work_days_from_joining.days + 1
        else:
            work_days = work_days_from_payslip.days + 1
        month_days = calendar.monthrange(year, month)[1]
        return month, year, float(work_days), float(month_days)

    def calc_income_tax_deduction(self, contract, payslip, categories, LR=0.0):
        date_from = payslip.date_from
        date_to = payslip.date_to
        joining_date = contract.date_start
        month, year, work_days, month_days = self._cal_date(date_from, date_to, joining_date)
        p_year = 0
        n_year = 0
        if month in [7, 8, 9, 10, 11, 12]:
            p_year = year
            n_year = year + 1
        else:
            p_year = year - 1
            n_year = year

        joining_month = datetime(joining_date.year, joining_date.month, 1)
        slabs_pool = self.env['tax.slab']
        basic = categories.BASIC or 0.0
        amount_gross = (categories.BASIC + categories.ALW)
        gross = amount_gross - LR
        slabs = slabs_pool.search([('state', '=', 'Active'),('company_id','=',contract.employee_id.company_id.id)])
        global annual_salary, month_tax
        annual_salary = 0.0
        month_tax = 0.0
        tax = 0.0
        if not slabs:
            raise ValidationError('Please define tax chart in payroll configuration')
        if len(slabs) > 1:
            raise ValidationError('Found two active tax charts')
        working_months = self.diff_month(date_from, joining_month)
        current_fy_june = datetime(n_year, 6, 1)
        if working_months + 1 >= 12:
            annual_salary = gross * 12.0
            month_tax = 12.0
        else:
            # if joining_month > datetime(joining_month.year,6,1):
            # print(joining_month , current_fy_june,'monthfghjm')
            if joining_month < current_fy_june:
                working_months_wtf_june = self.diff_month(current_fy_june, joining_month)
                if working_months_wtf_june >= 12:
                    payslips=self.env['hr.payslip'].search([('id','!=',payslip.id),('date_from','>=',slabs.date_from)])
                    pervious = 0
                    remaining = 0
                    for payslip_rec in payslips:
                        for line in payslip_rec.line_ids.filtered(lambda x:x.code=='GROSS'):
                            pervious+=line.amount
                    if payslip.date_from.month>=1:
                        remaining=6-payslip.date_from.month
                    if payslip.date_from.month>=7:
                        remaining=18-date_from.month

                    annual_salary = pervious+(gross * remaining)
                    month_tax = 12
                else:
                    payslips=self.env['hr.payslip'].search([('id','!=',payslip.id),('date_from','>=',slabs.date_from)])
                    pervious = 0
                    remaining = 0
                    for payslip_rec in payslips:
                        for line in payslip_rec.line_ids.filtered(lambda x:x.code=='GROSS'):
                            pervious+=line.amount
                    # print(pervious)
                    if payslip.date_from.month>=1:
                        remaining=6-payslip.date_from.month
                    if payslip.date_from.month>=7:
                        remaining=18-date_from.month
                    annual_salary = pervious+ (contract.perivous_gross)+(gross * (remaining+1))
                    # annual_salary = pervious+ (contract.perivous_gross)+gross * float(working_months_wtf_june + 1)
                    month_tax = float(12)
                    # month_tax = float(working_months_wtf_june + 1)

        def get_tax_1(slab):
            low = slab.lower_limit
            up = slab.upper_limit
            no_upper_limit=slab.no_upper_limit
            ex_amount = 0.0
            tax = 0.0
            if annual_salary >= low and annual_salary <= up:
                ex_amount = float(annual_salary)-float(low)
                tax = (ex_amount/month_tax) * (slab.tax_rate / 100) + (slab.fix_amount/month_tax)
            elif annual_salary >= low and up == 0.0:
                ex_amount = float(annual_salary) - float(low)
                tax = (ex_amount) * (slab.tax_rate) + (slab.fix_amount)
            else:
                tax = 0.0
            return tax

        tax_applicable = 0.0
        output = list(set(map(get_tax_1, slabs.tax_slab_detail)))
        print(output,'output')
        if len(output) > 1:
            tax_applicable = output[1]
        else:
            tax_applicable = output[0]

        tax = round((tax_applicable / month_days) * work_days)
        return round(tax)



    def calc_income_tax_gross_total(self, contract, payslip, categories, LR=0.0):
        date_from = payslip.date_from
        date_to = payslip.date_to
        joining_date = contract.date_start
        slabs_pool = self.env['tax.slab']
        slabs = slabs_pool.search([('state', '=', 'Active'),('company_id','=',contract.employee_id.company_id.id)])
        month, year, work_days, month_days = self._cal_date(date_from, date_to, joining_date)
        month_, year_, work_days_, month_days_ = self._cal_date(slabs.date_from, slabs.date_to, joining_date)
        p_year = 0
        n_year = 0
        if month in [7, 8, 9, 10, 11, 12]:
            p_year = year
            n_year = year + 1
        else:
            p_year = year - 1
            n_year = year

        joining_month = datetime(joining_date.year, joining_date.month, 1)
        slabs_pool = self.env['tax.slab']
        basic = categories.BASIC or 0.0
        amount_gross = (categories.BASIC + categories.ALW)
        gross = amount_gross - LR
        slabs = slabs_pool.search([('state', '=', 'Active'),('company_id','=',contract.employee_id.company_id.id)])
        global annual_salary, month_tax
        annual_salary = 0.0
        month_tax = 0.0
        tax = 0.0
        if not slabs:
            raise ValidationError('Please define tax chart in payroll configuration')
        if len(slabs) > 1:
            raise ValidationError('Found two active tax charts')
        print(date_from,joining_month)
        working_months = self.diff_month(date_from, joining_month)
        print(joining_date.year, joining_date.month, 1, 'here',working_months,'months')
        current_fy_june = datetime(n_year, 6, 1)
        if working_months + 1 >= 12:
            annual_salary = gross * 12.0
            print(annual_salary,'annual salary')
            month_tax = 12.0
        else:
            # if joining_month > datetime(joining_month.year,6,1):
            # print(joining_month , current_fy_june,'monthfghjm')
            if joining_month < current_fy_june:
                working_months_wtf_june = self.diff_month(current_fy_june, joining_month)
                if working_months_wtf_june >= 12:
                    payslips=self.env['hr.payslip'].search([('id','!=',payslip.id),('date_from','>=',slabs.date_from)])
                    pervious = 0
                    remaining = 0
                    for payslip_rec in payslips:
                        for line in payslip_rec.line_ids.filtered(lambda x:x.code=='GROSS'):
                            pervious+=line.amount
                    if payslip.date_from.month>=1:
                        remaining=6-payslip.date_from.month
                    if payslip.date_from.month>=7:
                        remaining=18-date_from.month

                    annual_salary = pervious+(gross * remaining)
                    month_tax = 12
                else:
                    print((contract.perivous_gross)+gross * float(working_months_wtf_june + 1),'Previous Annual')
                    payslips=self.env['hr.payslip'].search([('id','!=',payslip.id),('date_from','>=',slabs.date_from)])
                    pervious = 0
                    remaining = 0
                    for payslip_rec in payslips:
                        for line in payslip_rec.line_ids.filtered(lambda x:x.code=='GROSS'):
                            pervious+=line.amount
                    # print(pervious)
                    if payslip.date_from.month>=1:
                        remaining=6-payslip.date_from.month
                    if payslip.date_from.month>=7:
                        remaining=18-date_from.month
                    print(pervious,(remaining),gross , float(working_months_wtf_june + 1))
                    annual_salary = pervious+ (contract.perivous_gross)+(gross * (remaining+1))
                    # annual_salary = pervious+ (contract.perivous_gross)+gross * float(working_months_wtf_june + 1)
                    month_tax = float(12)
                    # month_tax = float(working_months_wtf_june + 1)

        def get_tax(slab):
            low = slab.lower_limit
            up = slab.upper_limit
            no_upper_limit=slab.no_upper_limit
            ex_amount = 0.0
            tax = 0.0
            print(annual_salary)
            if annual_salary >= low and annual_salary <= up:
                ex_amount = float(annual_salary)-float(low)
                print(ex_amount,month_tax,slab.tax_rate)
                tax = (ex_amount) * (slab.tax_rate / 100) + (slab.fix_amount)
            elif annual_salary >= low and up == 0.0:
                ex_amount = float(annual_salary) - float(low)
                tax = (ex_amount) * (slab.tax_rate) + (slab.fix_amount)
            else:
                tax = 0.0
            return tax

        tax_applicable = 0.0
        output = list(set(map(get_tax, slabs.tax_slab_detail)))
        if len(output) > 1:
            tax_applicable = output[1]
        else:
            tax_applicable = output[0]
        tax = round((tax_applicable / month_days_) * work_days_)
        return tax_applicable

    def calc_income_gross_total(self, contract, payslip, categories, LR=0.0):
        date_from = payslip.date_from
        date_to = payslip.date_to
        joining_date = contract.date_start
        slabs_pool = self.env['tax.slab']
        slabs = slabs_pool.search([('state', '=', 'Active'),('company_id','=',contract.employee_id.company_id.id)])
        month, year, work_days, month_days = self._cal_date(date_from, date_to, joining_date)
        p_year = 0
        n_year = 0
        if month in [7, 8, 9, 10, 11, 12]:
            p_year = year
            n_year = year + 1
        else:
            p_year = year - 1
            n_year = year

        joining_month = datetime(joining_date.year, joining_date.month, 1)
        slabs_pool = self.env['tax.slab']
        basic = categories.BASIC or 0.0
        amount_gross = (categories.BASIC + categories.ALW)
        gross = amount_gross - LR
        slabs = slabs_pool.search([('state', '=', 'Active'),('company_id','=',contract.employee_id.company_id.id)])
        global annual_salary, month_tax
        annual_salary = 0.0
        month_tax = 0.0
        tax = 0.0
        if not slabs:
            raise ValidationError('Please define tax chart in payroll configuration')
        if len(slabs) > 1:
            raise ValidationError('Found two active tax charts')
        print(date_from,joining_month)
        working_months = self.diff_month(date_from, joining_month)
        current_fy_june = datetime(n_year, 6, 1)
        if working_months + 1 >= 12:
            annual_salary = gross * 12.0
            print(annual_salary,'annual salary')
            month_tax = 12.0
        else:
            # if joining_month > datetime(joining_month.year,6,1):
            # print(joining_month , current_fy_june,'monthfghjm')
            print(joining_month,current_fy_june)
            if joining_month < current_fy_june:
                working_months_wtf_june = self.diff_month(current_fy_june, joining_month)
                if working_months_wtf_june >= 12:
                    payslips=self.env['hr.payslip'].search([('id','!=',payslip.id),('date_from','>=',slabs.date_from)])
                    pervious = 0
                    remaining = 0
                    for payslip_rec in payslips:
                        for line in payslip_rec.line_ids.filtered(lambda x:x.code=='GROSS'):
                            pervious+=line.amount
                    if payslip.date_from.month>=1:
                        remaining=6-payslip.date_from.month
                    if payslip.date_from.month>=7:
                        remaining=18-date_from.month

                    annual_salary = pervious+(gross * remaining)
                    month_tax = 12
                else:
                    payslips=self.env['hr.payslip'].search([('id','!=',payslip.id),('date_from','>=',slabs.date_from)])
                    pervious = 0
                    remaining = 0
                    for payslip_rec in payslips:
                        for line in payslip_rec.line_ids.filtered(lambda x:x.code=='GROSS'):
                            pervious+=line.amount
                    if payslip.date_from.month>=1:
                        remaining=6-payslip.date_from.month
                    if payslip.date_from.month>=7:
                        remaining=18-date_from.month
                    annual_salary = pervious+ (contract.perivous_gross)+(gross * (remaining+1))
                    print(annual_salary)
                    # annual_salary = pervious+ (contract.perivous_gross)+gross * float(working_months_wtf_june + 1)
                    month_tax = float(12)
        return annual_salary

    def TaxReceived(self, contract, payslip, categories, LR=0.0):
        slabs_pool = self.env['tax.slab']
        slabs = slabs_pool.search([('state', '=', 'Active'),('company_id','=',contract.employee_id.company_id.id)])
        payslips=self.env['hr.payslip'].search([('id','!=',payslip.id),('employee_id','=',contract.employee_id.id),('date_from','>=',slabs.date_from),('date_to','<=',slabs.date_to)])
        tax=0
        for line in payslips.line_ids:
            if line.category_id.code=='INCT':
                tax += line.total
        return tax

    def TaxIncomeReceived(self, contract, payslip, categories, LR=0.0):
        slabs_pool = self.env['tax.slab']
        slabs = slabs_pool.search([('state', '=', 'Active'),('company_id','=',contract.employee_id.company_id.id)])
        payslips=self.env['hr.payslip'].search([('date_from','>=',slabs.date_from),('date_to','<=',slabs.date_to),('id','!=',payslip.id)])
        tax=0
        for line in self.env['hr.payslip.line'].search([('slip_id','in',payslips.ids),('category_id.name','=','Gross')]):
            tax+=line.total
        return tax

    def TotalTillDateCollected(self, contract, payslip, categories, LR=0.0,rule_code=False):
        slabs_pool = self.env['tax.slab']
        slabs = slabs_pool.search([('state', '=', 'Active'),('company_id','=',contract.employee_id.company_id.id)])
        payslips=self.env['hr.payslip'].search([('date_from','>=',slabs.date_from),('date_to','<=',slabs.date_to),('id','!=',payslip.id)])
        print(payslips)
        tax=0
        for line in payslips.line_ids:
            if line.code==rule_code:
                tax+=line.total
        # for line in self.env['hr.payslip.line'].search([('slip_id','in',payslips.ids),('category_id.code','=',rule_code)]):
        #     tax+=line.total
        return tax

    def GetDeductions(self,code,contract_id):
        for line in contract_id.deduction_ids.filtered(lambda x:x.deduction_id.code==code):
            return line.amount
        return 0

    def GetAllowance(self,code,contract_id):
        for line in contract_id.allowance_ids.filtered(lambda x:x.allowance_id.code==code):
            return line.amount
        return 0

    perivous_gross_tax=fields.Float(string='Previous Gross Tax')
    perivous_gross=fields.Float(string='Previous Gross Salary')
    allowance_ids=fields.One2many('contract.allowance','contract_id')
    deduction_ids=fields.One2many('contract.deduction','contract_id')

    # def write(self,vals):
    #     rate=0
    #     for line in self.allowance_ids:
    #         rate+=line.amount
    #     if rate!=100:
    #         raise ValidationError('Some off all salary component must be equal to 100%')

class AllowanceAllowance(models.Model):
    _name = 'allowance.allowance'

    name=fields.Char(string='Allowance')
    code=fields.Char(string='Code')

class DeductionDedution(models.Model):
    _name = 'deduction.deduction'

    name=fields.Char(string='Deduction')
    code=fields.Char(string='Code')

class ContractAllowance(models.Model):
    _name = 'contract.allowance'

    struct_id=fields.Many2one('hr.payroll.structure',compute='GetPayrollStructure')
    rule_id=fields.Many2one('hr.salary.rule',domain="[('struct_id','=',struct_id)]")
    contract_id=fields.Many2one('hr.contract')
    allowance_id =fields.Many2one('hr.salary.rule', domain="[('category_id.code','in',('ALW','BASIC'))]")
    amount_percentage=fields.Float(string='Percentage')
    amount=fields.Float(string='Amount', compute='compute_amount', store=1)
    is_active=fields.Boolean('Active')

    @api.depends('amount_percentage')
    def compute_amount(self):
        for rec in self:
            if rec.contract_id.wage > 0.0:
                rec.amount = rec.contract_id.wage * (rec.amount_percentage / 100)



    def GetPayrollStructure(self):
        for rec in self:
            struct_id=self.env['hr.payroll.structure'].search([('type_id','=',self.contract_id.structure_type_id.id)])
            rec.struct_id=struct_id.id

class ContractDecudtion(models.Model):
    _name = 'contract.deduction'

    contract_id=fields.Many2one('hr.contract')
    deduction_id=fields.Many2one('hr.salary.rule', domain="[('category_id.code','=','DED')]")
    amount_percentage = fields.Float(string='Percentage')
    amount=fields.Float(string='Amount',compute='compute_amount', store=1)
    is_active=fields.Boolean('Active')

    @api.depends('amount_percentage')
    def compute_amount(self):
        for rec in self:
            if rec.contract_id.wage > 0.0:
                rec.amount = rec.contract_id.wage * (rec.amount_percentage / 100)