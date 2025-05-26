def post_init_hook(cr, registry):
    """Verify dependencies on module installation"""
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    checker = env['dependency.checker'].create({})
    try:
        checker.check_python_dependencies()
        checker.check_system_dependencies()
    except Exception as e:
        raise Exception(
            f"Dependency check failed. Please install requirements:\n\n"
            f"Python: pip install pytesseract opencv-python pymupdf numpy pillow\n"
            f"System: sudo apt install tesseract-ocr\n\n"
            f"Original error: {str(e)}"
        )
