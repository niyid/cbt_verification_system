from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    deepseek_api_key = fields.Char(
        string='DeepSeek API Key',
        config_parameter='deepseek.api_key',
        help="API key for DeepSeek marking service"
    )
    
    deepseek_api_url = fields.Char(
        string='DeepSeek API URL',
        config_parameter='deepseek.api_url',
        default="https://api.deepseek.com/v1/marking",
        help="Endpoint for DeepSeek marking API"
    )
    
    deepseek_timeout = fields.Integer(
        string='API Timeout (seconds)',
        config_parameter='deepseek.timeout',
        default=30,
        help="Timeout for API calls in seconds"
    )
