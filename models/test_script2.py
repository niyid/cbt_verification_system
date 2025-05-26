import requests
import base64
import logging
import json
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class TestScript(models.Model):
    _name = 'test.script'
    _description = 'Test Script with DeepSeek AI Marking'
    
    # Existing fields
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('test.script'))
    test_name = fields.Char(string='Test Name', required=True)
    exam_number = fields.Char(string='Exam Number', required=True)
    script_file = fields.Binary(string='Script File', required=True)
    file_name = fields.Char(string='File Name')
    file_type = fields.Selection([
        ('pdf', 'PDF'),
        ('jpeg', 'JPEG'),
        ('jpg', 'JPG'),
        ('png', 'PNG'),
    ], string='File Type', compute='_compute_file_type', store=True)
    original_score = fields.Float(string='Original Score')
    ai_score = fields.Float(string='AI Score')
    scoring_complete = fields.Boolean(string='Scoring Complete', default=False)
    complaint_id = fields.Many2one('test.complaint', string='Related Complaint')
    
    # DeepSeek specific fields
    deepseek_request = fields.Text(string='DeepSeek Request', readonly=True)
    deepseek_response = fields.Text(string='DeepSeek Response', readonly=True)
    deepseek_last_call = fields.Datetime(string='Last API Call', readonly=True)
    deepseek_status = fields.Selection([
        ('not_called', 'Not Called'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='API Status', default='not_called', readonly=True)
    
    @api.depends('file_name')
    def _compute_file_type(self):
        for record in self:
            if record.file_name:
                ext = record.file_name.lower().split('.')[-1]
                record.file_type = ext if ext in ['pdf', 'jpeg', 'jpg', 'png'] else False
    
    def _get_deepseek_api_key(self):
        """Retrieve DeepSeek API key from system parameters"""
        api_key = self.env['ir.config_parameter'].sudo().get_param('deepseek.api_key')
        if not api_key:
            raise UserError(_("DeepSeek API key is not configured. Please contact your system administrator."))
        return api_key
    
    def _get_deepseek_api_url(self):
        """Get the appropriate DeepSeek API endpoint"""
        return "https://api.deepseek.com/v1/marking"  # Replace with actual DeepSeek endpoint
    
    def _prepare_deepseek_payload(self):
        """Prepare the payload for DeepSeek API"""
        self.ensure_one()
        
        if not self.script_file:
            raise UserError(_("No script file uploaded for processing"))
        
        if not self.file_type:
            raise UserError(_("Could not determine file type from filename"))
        
        # Encode file content
        file_content = base64.b64decode(self.script_file)
        
        # Prepare metadata
        metadata = {
            "test_name": self.test_name,
            "exam_number": self.exam_number,
            "original_score": self.original_score,
            "odoo_record_id": self.id,
            "timestamp": fields.Datetime.now(),
        }
        
        return {
            "file_content": base64.b64encode(file_content).decode('utf-8'),
            "file_name": self.file_name,
            "file_type": self.file_type,
            "metadata": metadata,
            "scoring_parameters": {
                "strictness": "standard",  # Can be 'lenient', 'standard', 'strict'
                "partial_credit": True,
                "show_working": True,
            }
        }
    
    def _call_deepseek_api(self):
        """Make the actual API call to DeepSeek"""
        self.ensure_one()
        
        api_url = self._get_deepseek_api_url()
        api_key = self._get_deepseek_api_key()
        payload = self._prepare_deepseek_payload()
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        try:
            # Log the request
            self.write({
                'deepseek_request': json.dumps(payload, indent=2),
                'deepseek_last_call': fields.Datetime.now(),
            })
            
            # Make the API call
            start_time = datetime.now()
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30  # 30 seconds timeout
            )
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Process response
            response.raise_for_status()
            response_json = response.json()
            
            # Log the response
            self.write({
                'deepseek_response': json.dumps(response_json, indent=2),
                'deepseek_status': 'success',
            })
            
            _logger.info(
                f"DeepSeek API call successful for {self.name}. "
                f"Response time: {response_time:.2f}s. "
                f"Test: {self.test_name}, Exam: {self.exam_number}"
            )
            
            return response_json
            
        except requests.exceptions.RequestException as e:
            error_msg = f"DeepSeek API Error: {str(e)}"
            if hasattr(e, 'response') and e.response:
                error_msg += f"\nResponse: {e.response.text}"
            
            self.write({
                'deepseek_response': error_msg,
                'deepseek_status': 'failed',
            })
            
            _logger.error(error_msg)
            raise UserError(_("Failed to process script with DeepSeek: %s") % str(e))
    
    def _process_deepseek_response(self, response):
        """Process the response from DeepSeek API"""
        self.ensure_one()
        
        if not response.get('success'):
            raise UserError(_("DeepSeek API returned an error: %s") % response.get('error', 'Unknown error'))
        
        # Extract scores and feedback
        ai_score = response.get('score')
        feedback = response.get('feedback', {})
        
        if ai_score is None:
            raise UserError(_("No score returned from DeepSeek API"))
        
        # Create a detailed feedback record
        feedback_vals = {
            'script_id': self.id,
            'total_score': ai_score,
            'score_breakdown': json.dumps(feedback.get('breakdown', {})),
            'comments': feedback.get('general_comments', ''),
            'suggestions': feedback.get('suggestions', ''),
        }
        self.env['test.script.feedback'].create(feedback_vals)
        
        return ai_score
    
    def action_process_script(self):
        """Full process to mark script using DeepSeek API"""
        for script in self:
            if script.scoring_complete:
                raise UserError(_("This script has already been processed"))
            
            try:
                # Call DeepSeek API
                response = script._call_deepseek_api()
                
                # Process the response
                ai_score = script._process_deepseek_response(response)
                
                # Update script record
                script.write({
                    'ai_score': ai_score,
                    'scoring_complete': True,
                })
                
                # Update related complaint if exists
                if script.complaint_id:
                    script.complaint_id.write({
                        'verified_score': ai_score,
                        'state': 'in_review',
                    })
                    script.complaint_id.message_post(
                        body=_("Script processed with DeepSeek AI. New score: %s") % ai_score
                    )
                
            except Exception as e:
                _logger.error(f"Error processing script {script.name}: {str(e)}")
                script.message_post(
                    body=_("Failed to process script: %s") % str(e)
                )
                raise
    
    def action_retry_failed(self):
        """Retry failed API calls"""
        for script in self.filtered(lambda s: s.deepseek_status == 'failed'):
            script.with_context(retry=True).action_process_script()
