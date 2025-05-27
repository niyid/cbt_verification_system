from odoo import models, fields, api

class RemarkWizard(models.TransientModel):
    _name = 'remark.wizard'
    _description = 'Re-mark Test Script Wizard'
    
    test_name = fields.Char(string='Test Name', required=True)
    exam_number = fields.Char(string='Exam Number', required=True)
    script_file = fields.Binary(string='Upload Script', required=True)
    file_name = fields.Char(string='File Name')
    original_score = fields.Float(string='Original Score')
    
    def action_remark(self):
        self.ensure_one()
        TestScript = self.env['test.script']
        TestComplaint = self.env['test.complaint']
        
        # Create test script record
        script = TestScript.create({
            'test_name': self.test_name,
            'exam_number': self.exam_number,
            'script_file': self.script_file,
            'file_name': self.file_name,
            'original_score': self.original_score,
        })
        
        # Check if there's a complaint for this test/exam
        complaint = TestComplaint.search([
            ('test_name', '=', self.test_name),
            ('exam_number', '=', self.exam_number),
        ], limit=1)
        
        if complaint:
            script.write({'complaint_id': complaint.id})
            complaint.write({'test_script_id': script.id, 'state': 'in_review'})
        
        # Process the script
        script.action_process_script()
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'test.script',
            'res_id': script.id,
            'view_mode': 'form',
            'target': 'current',
        }
