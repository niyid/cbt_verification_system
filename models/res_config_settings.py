from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # DeepSeek API Configuration fields
    deepseek_api_key = fields.Char(
        string="DeepSeek API Key",
        config_parameter='deepseek.api_key',
        help="API key for DeepSeek marking service"
    )
    
    deepseek_api_url = fields.Char(
        string="DeepSeek API URL",
        config_parameter='deepseek.api_url',
        default='https://api.deepseek.com/v1',
        help="Endpoint for DeepSeek API"
    )
    
    deepseek_timeout = fields.Integer(
        string="DeepSeek Timeout",
        config_parameter='deepseek.timeout',
        default=30,
        help="Timeout in seconds for API calls"
    )

    # Computed fields that are referenced in the XML views
    company_count = fields.Integer(
        string="Number of Companies",
        compute='_compute_company_count'
    )
    
    company_informations = fields.Text(
        string="Company Information",
        compute='_compute_company_informations'
    )
    
    language_count = fields.Integer(
        string="Number of Languages",
        compute='_compute_language_count'
    )
    
    active_user_count = fields.Integer(
        string="Number of Active Users",
        compute='_compute_active_user_count'
    )

    @api.depends('company_id')
    def _compute_company_count(self):
        for record in self:
            record.company_count = self.env['res.company'].search_count([])

    @api.depends('company_id')
    def _compute_company_informations(self):
        for record in self:
            company = record.company_id or self.env.company
            info_parts = []
            if company.email:
                info_parts.append(company.email)
            if company.phone:
                info_parts.append(company.phone)
            if company.website:
                info_parts.append(company.website)
            record.company_informations = ' | '.join(info_parts) if info_parts else ''

    def _compute_language_count(self):
        for record in self:
            record.language_count = self.env['res.lang'].search_count([('active', '=', True)])

    def _compute_active_user_count(self):
        for record in self:
            record.active_user_count = self.env['res.users'].search_count([
                ('active', '=', True),
                ('share', '=', False)
            ])

    def open_company(self):
        """Open company form view"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Company',
            'res_model': 'res.company',
            'res_id': self.company_id.id or self.env.company.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def open_default_user(self):
        """Open default user template form"""
        default_user = self.env.ref('base.default_user', raise_if_not_found=False)
        if not default_user:
            # Create default user template if it doesn't exist
            default_user = self.env['res.users'].create({
                'name': 'Default User Template',
                'login': 'default_user_template',
                'active': False,
                'is_template': True,
            })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Default User Template',
            'res_model': 'res.users',
            'res_id': default_user.id,
            'view_mode': 'form',
            'target': 'current',
        }
