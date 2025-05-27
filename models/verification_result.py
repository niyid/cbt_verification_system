# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VerificationResult(models.Model):
    _name = 'verification.result'
    _description = 'Test Verification Results'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Fields
    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New'),
        copy=False
    )
    complaint_id = fields.Many2one(
        'test.complaint',
        string='Related Complaint',
        required=True,
        ondelete='cascade'
    )
    test_script_id = fields.Many2one(
        'test.script',
        string='Test Script',
        related='complaint_id.test_script_id',
        store=True
    )
    exam_number = fields.Char(
        string='Exam Number',
        related='complaint_id.exam_number',
        store=True
    )
    test_name = fields.Char(
        string='Test Name',
        related='complaint_id.test_name',
        store=True
    )
    original_score = fields.Float(
        string='Original Score',
        related='complaint_id.original_score',
        store=True
    )
    verified_score = fields.Float(
        string='Verified Score',
        related='complaint_id.verified_score',
        store=True
    )
    score_difference = fields.Float(
        string='Score Difference',
        compute='_compute_score_difference',
        store=True
    )
    status = fields.Selection([
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('disputed', 'Disputed'),
        ('final', 'Final'),
    ], string='Status', default='pending', tracking=True)
    verification_method = fields.Selection([
        ('auto', 'Automatic (AI)'),
        ('manual', 'Manual Review'),
        ('hybrid', 'Hybrid (AI + Manual)'),
    ], string='Verification Method')
    verification_date = fields.Datetime(
        string='Verification Date',
        default=fields.Datetime.now
    )
    verified_by = fields.Many2one(
        'res.users',
        string='Verified By',
        default=lambda self: self.env.user
    )
    notes = fields.Text(string='Verification Notes')
    feedback_ids = fields.One2many(
        'test.script.feedback',
        'verification_id',
        string='Detailed Feedback'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Supporting Documents'
    )

    # Constraints
    @api.constrains('verified_score')
    def _check_score_range(self):
        for record in self:
            if record.verified_score < 0 or record.verified_score > 100:
                raise ValidationError(_("Verified score must be between 0 and 100"))

    # Computed fields
    @api.depends('original_score', 'verified_score')
    def _compute_score_difference(self):
        for record in self:
            record.score_difference = record.verified_score - record.original_score

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('verification.result') or _('New')
        return super().create(vals_list)

    # Action methods
    def action_mark_verified(self):
        self.write({
            'status': 'verified',
            'verification_date': fields.Datetime.now(),
            'verified_by': self.env.user.id
        })
        self._send_status_notification()

    def action_mark_disputed(self):
        self.ensure_one()
        return {
            'name': _('Dispute Details'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'verification.dispute.wizard',
            'target': 'new',
            'context': {
                'default_verification_id': self.id,
            }
        }

    def action_mark_final(self):
        self.write({'status': 'final'})
        self.complaint_id.action_resolve()
        self._send_final_notification()

    # Business logic
    def _send_status_notification(self):
        template = self.env.ref('cbt_verification_system.email_template_verification_status')
        for record in self:
            template.send_mail(record.id, force_send=True)

    def _send_final_notification(self):
        template = self.env.ref('cbt_verification_system.email_template_verification_final')
        for record in self:
            template.send_mail(record.id, force_send=True)

    def generate_verification_report(self):
        """Generate PDF report of verification results"""
        self.ensure_one()
        return {
            'type': 'ir.actions.report',
            'report_name': 'cbt_verification_system.verification_report',
            'model': 'verification.result',
            'report_type': 'qweb-pdf',
            'context': {'active_id': self.id},
        }
