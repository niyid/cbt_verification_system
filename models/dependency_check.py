import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class DependencyChecker(models.Model):
    _name = 'dependency.checker'
    _description = 'System Dependency Verification'

    def check_python_dependencies(self):
        """Verify all required Python packages are installed"""
        dependencies = {
            'pytesseract': '0.3.10',
            'cv2': '4.5.0',  # opencv-python
            'fitz': '1.18.0',  # pymupdf
            'numpy': '1.21.0',
            'PIL': '9.0.0'  # Pillow
        }
        
        missing = []
        for package, min_version in dependencies.items():
            try:
                mod = __import__(package)
                current_version = getattr(mod, '__version__', '0.0.0')
                if current_version < min_version:
                    missing.append(f"{package} (requires {min_version}+, found {current_version})")
            except ImportError:
                missing.append(package)
        
        if missing:
            raise UserError(_(
                "Missing or outdated Python dependencies:\n\n- %s\n\n"
                "Please install using:\n\n"
                "pip install pytesseract opencv-python pymupdf numpy pillow --upgrade"
            ) % "\n- ".join(missing))
        
        return True

    def check_system_dependencies(self):
        """Verify system-level dependencies"""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except (ImportError, pytesseract.TesseractNotFoundError):
            raise UserError(_(
                "Tesseract OCR not found. Please install system packages:\n\n"
                "Linux: sudo apt install tesseract-ocr\n"
                "MacOS: brew install tesseract"
            ))
