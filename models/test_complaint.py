from odoo import models, fields, api
import re
from odoo.exceptions import ValidationError

class TestComplaint(models.Model):
    _name = 'test.complaint'
    _description = 'Test Result Complaint'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Complaint Reference', required=True, copy=False, readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('test.complaint'))
    test_name = fields.Char(string='Test Name', required=True)
    exam_number = fields.Char(string='Exam Number', required=True)
    applicant_name = fields.Char(string='Applicant Name')
    applicant_email = fields.Char(string='Applicant Email')
    complaint_details = fields.Text(string='Complaint Details')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('in_review', 'In Review'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)
    test_script_id = fields.Many2one('test.script', string='Test Script')
    original_score = fields.Float(string='Original Score')
    verified_score = fields.Float(string='Verified Score')
    difference = fields.Float(string='Score Difference', compute='_compute_difference')
    
    @api.depends('original_score', 'verified_score')
    def _compute_difference(self):
        for record in self:
            record.difference = record.verified_score - record.original_score
    
    @api.constrains('applicant_email')
    def _check_applicant_email(self):
        for record in self:
            if record.applicant_email and not re.match(record.applicant_email):
                raise ValidationError("Invalid email address format")
    
    def action_submit(self):
        for record in self:
            record.write({'state': 'submitted'})
            record._send_status_email()
    
    def action_review(self):
        for record in self:
            record.write({'state': 'in_review'})
            record._send_status_email()
    
    def action_resolve(self):
        for record in self:
            record.write({'state': 'resolved'})
            record._send_status_email()
    
    def action_reject(self):
        for record in self:
            record.write({'state': 'rejected'})
            record._send_status_email()
    
    def _send_status_email(self):
        self.ensure_one()
        template = self.env.ref('test_verification_system.email_template_complaint_status')
        template.send_mail(self.id, force_send=True)
