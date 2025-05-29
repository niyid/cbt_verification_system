{
    'name': 'CBT Verification System',
    'version': '18.0.1.0.0',
    'summary': 'Computer-Based Test Verification with AI Grading',
    'description': """
        Comprehensive test verification system with:
        - Complaint management
        - Multi-subject grading
        - DeepSeek AI integration
        - PDF/JPEG answer sheet processing
    """,
    'author': 'Techducat Limited',
    'website': 'https://www.techducat.com',
    'category': 'Education',
    'depends': ['base', 'web', 'mail', 'portal'],
    'external_dependencies': {
        'python': [
            'pytesseract>=0.3.10',
            'opencv-python>=4.5.0',
            'pymupdf>=1.18.0',
            'numpy>=1.21.0',
            'Pillow>=9.0.0'
        ],
        'bin': ['tesseract-ocr']
    },
    'data': [
        'views/menu_views.xml',
        'views/complaint_views.xml',
        'views/test_script_views.xml',
        'views/feedback_views.xml',
        'views/res_config_settings_views.xml',
        'views/portal_templates.xml',
        'wizard/remark_wizard.xml',
        'security/security_groups.xml',
        'data/mail_templates.xml',
        'security/ir.model.access.csv',
        'security/security_rules.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
