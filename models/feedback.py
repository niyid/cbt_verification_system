from odoo import models, fields, api

class TestScriptFeedback(models.Model):
    _name = 'test.script.feedback'
    _description = 'DeepSeek AI Feedback on Test Script'
    
    script_id = fields.Many2one('test.script', string='Script', required=True, ondelete='cascade')
    date_received = fields.Datetime(string='Date Received', default=fields.Datetime.now)
    total_score = fields.Float(string='Total Score')
    score_breakdown = fields.Text(string='Score Breakdown')
    comments = fields.Text(string='General Comments')
    suggestions = fields.Text(string='Suggestions for Improvement')
    
    def get_breakdown_dict(self):
        """Convert score breakdown JSON to dict"""
        try:
            return json.loads(self.score_breakdown) if self.score_breakdown else {}
        except json.JSONDecodeError:
            return {}
