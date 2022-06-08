from odoo import fields,models,api
import werkzeug
import base64
from odoo.exceptions import UserError, ValidationError

from datetime import datetime, timedelta, date

class InheritHRContract(models.Model):
    _inherit = 'hr.contract'

    proposal_sent=fields.Boolean()
    offer_letter_count=fields.Integer(compute='GetOfferLetter')

    def action_offer_letter(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract',
            'res_model': 'sign.template',
            'view_mode': 'tree,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {
                'active_test': False
            },
        }


    def GetOfferLetter(self):
        self.offer_letter_count=self.env['sign.template'].search_count([('contract_id','=',self.id)])

    def SendProposal(self):
        partner_id=self.employee_id.address_home_id
        print(partner_id)
        report_name = "nd_contracts_report.hr_contract_report"
        pdf = self.env["ir.actions.report"]._get_report_from_name(report_name)
        pdf._render_qweb_pdf([self.id])
        print(pdf._render_qweb_pdf([self.id]))
        attachment_id=self.env['ir.attachment'].search([], order="id desc",limit=1)
        print(attachment_id,'fghj')
        rec=self.env['sign.template'].create({'user_id':self.env.uid,'attachment_id':attachment_id.id,'redirect_url_text':'Open Link','contract_id':self.id})
        request=self.env['sign.send.request'].create({'filename':'Contract '+ self.employee_id.name,'signer_id':partner_id.id,'subject':'Contract:-'+self.employee_id.name,'template_id':rec.id})
        print(request)
        request.send_request()
        self.proposal_sent=True
        # self.report_file = report_output


class HrContractSignDocumentWizard1(models.TransientModel):
    _inherit = 'hr.contract.sign.document.wizard'

    @api.onchange('employee_id')
    def CreateDocument(self):
        report_name = "nd_contracts_report.hr_contract_report"
        pdf = self.env["ir.actions.report"]._get_report_from_name(report_name)
        attach=pdf._render_qweb_pdf([self.contract_id.id])
        print(attach)
        attachment_id=self.env['ir.attachment'].search([('res_id','=',self.id)], order="id desc",limit=1)
        self.sign_template_ids=self.env['sign.template'].create({'attachment_id':attachment_id.id,'redirect_url_text':'Open Link','contract_id':self.contract_id.id})


class InheritHrRecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    survey_id=fields.Many2one('survey.survey')
    contract_proposal_stage=fields.Boolean(string='Contract Proposal Stage')
    first_signatory=fields.Many2one('res.partner',string='First Signatory')
    interviewer_template_id=fields.Many2one('mail.template')

class InheritSurveySurvey(models.Model):
    _inherit = 'survey.user_input'

    applicant_id=fields.Many2one('hr.applicant')
    stage_id=fields.Many2one('hr.recruitment.stage',string='Rule')

class InheritSurveySurvey(models.Model):
    _inherit = 'survey.survey'

    def _create_answer(self,stage_id=False,applicant_id=False, user=False, partner=False, email=False, test_entry=False, check_attempts=True, **additional_vals):
        """ Main entry point to get a token back or create a new one. This method
        does check for current user access in order to explicitely validate
        security.

          :param user: target user asking for a token; it might be void or a
                       public user in which case an email is welcomed;
          :param email: email of the person asking the token is no user exists;
        """
        self.check_access_rights('read')
        self.check_access_rule('read')

        user_inputs = self.env['survey.user_input']
        for survey in self:
            if partner and not user and partner.user_ids:
                user = partner.user_ids[0]

            invite_token = additional_vals.pop('invite_token', False)
            survey._check_answer_creation(user, partner, email, test_entry=test_entry, check_attempts=check_attempts, invite_token=invite_token)
            answer_vals = {
                'applicant_id':applicant_id,
                'survey_id': survey.id,
                'test_entry': test_entry,
                'stage_id':stage_id,
                'is_session_answer': survey.session_state in ['ready', 'in_progress']
            }
            if survey.session_state == 'in_progress':
                # if the session is already in progress, the answer skips the 'new' state
                answer_vals.update({
                    'state': 'in_progress',
                    'start_datetime': fields.Datetime.now(),
                })
            if user and not user._is_public():
                answer_vals['partner_id'] = user.partner_id.id
                answer_vals['email'] = user.email
                answer_vals['nickname'] = user.name
            elif partner:
                answer_vals['partner_id'] = partner.id
                answer_vals['email'] = partner.email
                answer_vals['nickname'] = partner.name
            else:
                answer_vals['email'] = email
                answer_vals['nickname'] = email

            if invite_token:
                answer_vals['invite_token'] = invite_token
            elif survey.is_attempts_limited and survey.access_mode != 'public':
                # attempts limited: create a new invite_token
                # exception made for 'public' access_mode since the attempts pool is global because answers are
                # created every time the user lands on '/start'
                answer_vals['invite_token'] = self.env['survey.user_input']._generate_invite_token()

            answer_vals.update(additional_vals)
            user_inputs += user_inputs.create(answer_vals)

        for question in self.mapped('question_ids').filtered(
                lambda q: q.question_type == 'char_box' and (q.save_as_email or q.save_as_nickname)):
            for user_input in user_inputs:
                if question.save_as_email and user_input.email:
                    user_input.save_lines(question, user_input.email)
                if question.save_as_nickname and user_input.nickname:
                    user_input.save_lines(question, user_input.nickname)

        return user_inputs

class InheritJobPosition(models.Model):
    _inherit = 'hr.job'

    res_manager_id=fields.Many2one('res.users',string='Hiring Manager')
    recruiter_id=fields.Many2one('res.users',string='Recruiter/HR Head')
    # hiring_manager_id=fields.Many2one('res.users',string='Recruiter/HR Head')
    department_manager_id=fields.Many2one('res.users',string='Chief of the Department')
    last_interview_id=fields.Many2one('res.users',string='4th Interviewer')

class InheritHrApplicant(models.Model):
    _inherit = 'hr.applicant'

    res_manager_id=fields.Many2one('res.users',string='Hiring Manager',compute='GetInterviewerDetails',store=True)
    recruiter_id=fields.Many2one('res.users',string='Recruiter/HR Head',compute='GetInterviewerDetails',store=True)
    department_manager_id=fields.Many2one('res.users',string='	Chief of the Department',compute='GetInterviewerDetails',store=True)
    last_interview_id=fields.Many2one('res.users',string='4th Interviewer',compute='GetInterviewerDetails',store=True)
    recruiter_head_survey=fields.Boolean(compute='GetInterviewState')
    hiring_manager_survey=fields.Boolean(compute='GetInterviewState')
    department_chief_survey=fields.Boolean(compute='GetInterviewState')
    last_interview_survey=fields.Boolean(compute='GetInterviewState')
    interview_count=fields.Integer(compute='GetInterviewState')
    report_file=fields.Binary()
    check_proposal_stage=fields.Boolean(compute='GetProposalStatus')
    check_offer_letter_stage=fields.Boolean(compute='GetProposalStatus')
    proposal_sent=fields.Boolean()
    offer_letter=fields.Boolean()
    offer_letter_count=fields.Integer(compute='GetOfferLetter')
    applicant_email=fields.Boolean(string='Email To Applicant',default=True)

    def _track_template(self, changes):
        # res = super(InheritHrApplicant, self)._track_template(changes)
        applicant = self[0]
        res={}
        print(applicant,res)
        if applicant.applicant_email:
            if 'stage_id' in changes and applicant.stage_id.template_id:
                res['stage_id'] = (applicant.stage_id.template_id, {
                    'auto_delete_message': True,
                    'subtype_id': self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
                    'email_layout_xmlid': 'mail.mail_notification_light'
                })
        if applicant.stage_id.interviewer_template_id:
            res['user_id'] = (applicant.stage_id.interviewer_template_id, {
                'auto_delete_message': True,
                'subtype_id': self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
                'email_layout_xmlid': 'mail.mail_notification_light'
            })
        return res

    def GetOfferLetter(self):
        self.offer_letter_count=self.env['sign.template'].search_count([('applicant_id','=',self.id)])


    def GetProposalStatus(self):
        self.check_proposal_stage=False
        self.check_offer_letter_stage=False
        if self.stage_id.first_signatory and self.proposal_sent==False:
            self.check_proposal_stage=True
        rec=self.env['sign.template'].search([('applicant_id','=',self.id)])
        request=self.env['sign.request'].search([('template_id','=',rec.id)])
        if self.check_proposal_stage==False and request.state=='signed':
            self.check_offer_letter_stage=True
    def SendProposal(self):
        self.partner_id=self.env['res.partner'].create({'email': self.email_from,'name':self.name})
        report_name = "hiring_recuritment.offer_letter_report"
        # pdf = self.env["ir.actions.report"]._get_report_from_name(report_name)
        pdf = self.env.ref('hiring_recuritment.offer_letter_report_ids')._render_qweb_pdf(self.ids)
        # pdf._render_qweb_pdf([self.id])
        attachment_id=self.env['ir.attachment'].search([('res_id','=',self.id),('res_model','=','hr.applicant')], order="id desc",limit=1)
        rec=self.env['sign.template'].create({'attachment_id':attachment_id.id,'redirect_url_text':'Open Link','applicant_id':self.id})
        request=self.env['sign.send.request'].create({'filename':'Offer letter of '+ self.partner_id.name,'signer_id':self.stage_id.first_signatory.id,'subject':'Offer latter:-'+self.partner_id.name,'template_id':rec.id})
        request.send_request()
        self.proposal_sent=True
        # self.report_file = report_output

    def SendOfferLeeter(self):
        rec=self.env['sign.template'].search([('applicant_id','=',self.id)])
        request=self.env['sign.request'].search([('template_id','=',rec.id)])
        request.state='sent'
        item=self.env['sign.request.item'].create({'sign_request_id':request.id,'partner_id':self.partner_id.id})
        item.send_signature_accesses()
        item.state='sent'
        # request_1=self.env['sign.send.request'].create({'filename':'Offer letter of '+ self.partner_id.name,'signer_id':self.partner_id.id,'subject':'Offer latter:-'+self.partner_id.name,'template_id':rec.id})
        # request_1.send_request()
        self.offer_letter=True

    def ApplicationRefuse(self):
        for rec in self:
            self.write({'active': False})
            # applicants = self.applicant_ids.filtered(lambda x: x.email_from or x.partner_id.email)
            template_id=self.env['mail.template'].search([('name','=','Rejection Email')],limit=1)
            if template_id:
                rec.message_post_with_template(template_id.id, **{
                    'auto_delete_message': True,
                    'subtype_id': self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
                    'email_layout_xmlid': 'mail.mail_notification_light'
                })
    def SetOnHold(self):
        for rec in self:
            # self.write({'active': False})
            # applicants = self.applicant_ids.filtered(lambda x: x.email_from or x.partner_id.email)
            rec.stage_id = self.env['hr.recruitment.stage'].search([('name', '=', 'On Hold')], limit=1).id

    def forward_to_next_stage(self):
        for rec in self:
            if rec.stage_id.name=='3rd Interview':
                rec.stage_id=self.env['hr.recruitment.stage'].search([('name','=','4th Interviewer')],limit=1).id
            if rec.stage_id.name=='2nd Interview':
                rec.stage_id=self.env['hr.recruitment.stage'].search([('name','=','3rd Interview')],limit=1).id
            if rec.stage_id.name=='1st Interview':
                rec.stage_id=self.env['hr.recruitment.stage'].search([('name','=','2nd Interview')],limit=1).id
            if rec.stage_id.name=='Initial Qualification':
                rec.stage_id=self.env['hr.recruitment.stage'].search([('name','=','1st Interview')],limit=1).id

    def backward_to_next_stage(self):
        for rec in self:
            if rec.stage_id.name=='1st Interview':
                rec.stage_id=self.env['hr.recruitment.stage'].search([('name','=','Initial Qualification')],limit=1).id
            if rec.stage_id.name=='2nd Interview':
                rec.stage_id=self.env['hr.recruitment.stage'].search([('name','=','1st Interview')],limit=1).id
            if rec.stage_id.name=='3rd Interview':
                rec.stage_id=self.env['hr.recruitment.stage'].search([('name','=','2nd Interview')],limit=1).id
            if rec.stage_id.name=='4th Interviewer':
                rec.stage_id=self.env['hr.recruitment.stage'].search([('name','=','3rd Interview')],limit=1).id




    def action_applications_interview(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Job Interview',
            'res_model': 'survey.user_input',
            'view_mode': 'tree,form,pivot,graph',
            'domain': [('applicant_id', '=', self.id)],
            'context': {
                'active_test': False
            },
        }
    def action_offer_letter(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Offer Letter',
            'res_model': 'sign.template',
            'view_mode': 'tree,form',
            'domain': [('applicant_id', '=', self.id)],
            'context': {
                'active_test': False
            },
        }

    def GetInterviewState(self):
        for rec in self:
            rec.interview_count=self.env['survey.user_input'].search_count([('applicant_id', '=', rec.id)])
            rec.recruiter_head_survey=False
            rec.hiring_manager_survey=False
            rec.department_chief_survey=False
            rec.last_interview_survey=False
            if rec.stage_id.name=='1st Interview' and not self.env['survey.user_input'].search([('applicant_id', '=', rec.id),('stage_id', '=',rec.stage_id.id)]):
                rec.recruiter_head_survey = True
            if rec.stage_id.name=='2nd Interview' and not self.env['survey.user_input'].search([('applicant_id', '=', rec.id),('stage_id', '=',rec.stage_id.id)]):
                rec.hiring_manager_survey = True
            if rec.stage_id.name=='3rd Interview' and not self.env['survey.user_input'].search([('applicant_id', '=', rec.id),('stage_id', '=',rec.stage_id.id)]):
                rec.department_chief_survey = True
            if rec.stage_id.name=='4th Interview' and not self.env['survey.user_input'].search([('applicant_id', '=', rec.id),('stage_id', '=',rec.stage_id.id)]):
                rec.last_interview_survey = True

    @api.depends('job_id')
    def GetInterviewerDetails(self):
        for rec in self:
            rec.res_manager_id=rec.job_id.res_manager_id.id
            rec.recruiter_id=rec.job_id.recruiter_id.id
            rec.department_manager_id=rec.job_id.department_manager_id.id
            rec.last_interview_id=rec.job_id.last_interview_id.id

    def FillSurvey(self):
        # self.env['survey.user_input'].create({'applicant_id':self.id,'application_stage':self.stage_id.name,'partner_id':self.env.user.partner_id.id,
        #                                       'survey_id':self.stage_id.survey_id.id})
        if not self.stage_id.survey_id:
            raise ValidationError('Survey not configured against the stage')
        survey=self.stage_id.survey_id
        if not self.recruiter_head_survey:
            survey.action_open_session_manager()
            if self.env['survey.user_input'].sudo().search([('applicant_id', '=', self.id),
                                                            ('survey_id', '=', survey.id),
                                                             ('stage_id', '=',self.stage_id.id)]):
                return {
                    'type': 'ir.actions.act_url',
                    'name': "Applicant Survey",
                    'target': 'new',
                    'url': '/survey/start/' + survey.access_token + "?param=" + str(
                        self.env.user.partner_id.id)
                }
            else:
                answer = survey._create_answer(partner=self.env.user.partner_id,applicant_id=self.id,stage_id=self.stage_id.id)
                url = '%s?%s' % (survey.sudo().get_start_url(),
                                 werkzeug.urls.url_encode({'answer_token': answer and answer.access_token or None,
                                                           'param': self.env.user.partner_id.id}))
                self.GetInterviewState()
                return {
                    'type': 'ir.actions.act_url',
                    'name': "Applicant Survey",
                    'target': 'new',
                    'url': url,
                }
        if not self.hiring_manager_survey:
            survey.action_open_session_manager()
            if self.env['survey.user_input'].sudo().search([('applicant_id', '=', self.id),
                                                            ('survey_id', '=', survey.id),
                                                             ('stage_id', '=',self.stage_id.id)]):
                return {
                    'type': 'ir.actions.act_url',
                    'name': "Applicant Survey",
                    'target': 'new',
                    'url': '/survey/start/' + survey.access_token + "?param=" + str(
                        self.env.user.partner_id.id)
                }
            else:
                answer = survey._create_answer(partner=self.env.user.partner_id,applicant_id=self.id,stage_id=self.stage_id.id)
                url = '%s?%s' % (survey.sudo().get_start_url(),
                                 werkzeug.urls.url_encode({'answer_token': answer and answer.access_token or None,
                                                           'param': self.env.user.partner_id.id}))
                self.GetInterviewState()
                return {
                    'type': 'ir.actions.act_url',
                    'name': "Applicant Survey",
                    'target': 'new',
                    'url': url,
                }
        if not self.department_chief_survey:
            survey.action_open_session_manager()
            if self.env['survey.user_input'].sudo().search([('applicant_id', '=', self.id),
                                                            ('survey_id', '=', survey.id),
                                                             ('stage_id', '=',self.stage_id.id)]):
                return {
                    'type': 'ir.actions.act_url',
                    'name': "Applicant Survey",
                    'target': 'new',
                    'url': '/survey/start/' + survey.access_token + "?param=" + str(
                        self.env.user.partner_id.id)
                }
            else:
                answer = survey._create_answer(partner=self.env.user.partner_id,applicant_id=self.id,stage_id=self.stage_id.id)
                url = '%s?%s' % (survey.sudo().get_start_url(),
                                 werkzeug.urls.url_encode({'answer_token': answer and answer.access_token or None,
                                                           'param': self.env.user.partner_id.id}))
                self.GetInterviewState()
                return {
                    'type': 'ir.actions.act_url',
                    'name': "Applicant Survey",
                    'target': 'new',
                    'url': url,
                }
        if not self.last_interview_survey:
            survey.action_open_session_manager()
            if self.env['survey.user_input'].sudo().search([('applicant_id', '=', self.id),
                                                            ('survey_id', '=', survey.id),
                                                             ('stage_id', '=',self.stage_id.id)]):
                return {
                    'type': 'ir.actions.act_url',
                    'name': "Applicant Survey",
                    'target': 'new',
                    'url': '/survey/start/' + survey.access_token + "?param=" + str(
                        self.env.user.partner_id.id)
                }
            else:
                answer = survey._create_answer(partner=self.env.user.partner_id,applicant_id=self.id,stage_id=self.stage_id.id)
                url = '%s?%s' % (survey.sudo().get_start_url(),
                                 werkzeug.urls.url_encode({'answer_token': answer and answer.access_token or None,
                                                           'param': self.env.user.partner_id.id}))
                self.GetInterviewState()
                return {
                    'type': 'ir.actions.act_url',
                    'name': "Applicant Survey",
                    'target': 'new',
                    'url': url,
                }

class SignInherit(models.Model):
    _inherit = 'sign.template'

    applicant_id=fields.Many2one('hr.applicant')
    contract_id=fields.Many2one('hr.contract')


class InheritHRPlan(models.Model):
    _inherit = 'hr.plan'

    company_id=fields.Many2one('res.company')

class InheritHRPlanType(models.Model):
    _inherit = 'hr.plan.activity.type'

    company_id=fields.Many2one('res.company')