import io
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import pytesseract
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class TestScript(models.Model):
    _inherit = 'test.script'
    
    subject_type = fields.Selection([
        ('math', 'Mathematics'),
        ('english', 'English'),
        ('physics', 'Physics'),
        ('chemistry', 'Chemistry'),
        ('biology', 'Biology'),
        ('general', 'General Knowledge'),
    ], string='Subject Type', required=True)
    
    answer_key = fields.Binary('Answer Key File')
    answer_key_filename = fields.Char('Answer Key Filename')
    detected_answers = fields.Text('Detected Answers', readonly=True)
    processing_log = fields.Text('Processing Log', readonly=True)
    
    def _log_processing(self, message):
        """Add timestamped log entries"""
        timestamp = fields.Datetime.now()
        self.processing_log = f"{self.processing_log or ''}\n[{timestamp}] {message}"
    
    def _extract_from_pdf(self, file_data):
        """Extract marked answers from PDF answer sheets"""
        try:
            self._log_processing("Starting PDF processing")
            doc = fitz.open(stream=io.BytesIO(file_data))
            page = doc.load_page(0)
            
            # Enhanced processing for different answer sheet formats
            text = page.get_text("text")
            self._log_processing(f"Extracted raw text: {text[:500]}...")
            
            # Detect shaded bubbles (basic approach)
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            open_cv_image = np.array(img)
            gray_image = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
            
            # Thresholding for bubble detection
            _, threshold = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY_INV)
            contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            self._log_processing(f"Found {len(contours)} potential answer bubbles")
            return text, contours
            
        except Exception as e:
            self._log_processing(f"PDF processing failed: {str(e)}")
            raise UserError(_("PDF processing error: %s") % str(e))
    
    def _extract_from_image(self, file_data):
        """Process JPEG/PNG answer sheets"""
        try:
            self._log_processing("Starting image processing")
            image = Image.open(io.BytesIO(file_data))
            
            # Preprocessing for better OCR
            img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            
            # OCR with pytesseract
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(thresh, config=custom_config)
            self._log_processing(f"Extracted text: {text[:500]}...")
            
            # Bubble detection
            contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = contours[0] if len(contours) == 2 else contours[1]
            
            self._log_processing(f"Found {len(contours)} potential answer bubbles")
            return text, contours
            
        except Exception as e:
            self._log_processing(f"Image processing failed: {str(e)}")
            raise UserError(_("Image processing error: %s") % str(e))
    
    def _parse_answer_key(self):
        """Parse the uploaded answer key"""
        if not self.answer_key:
            raise UserError(_("No answer key provided"))
        
        key_data = base64.b64decode(self.answer_key)
        if self.answer_key_filename.lower().endswith('.pdf'):
            doc = fitz.open(stream=io.BytesIO(key_data))
            return doc.load_page(0).get_text()
        else:
            image = Image.open(io.BytesIO(key_data))
            return pytesseract.image_to_string(image)
    
    def _match_answers(self, detected_text, contours, answer_key):
        """Match detected answers to answer key with subject-specific logic"""
        try:
            self._log_processing("Starting answer matching")
            
            # Subject-specific processing
            if self.subject_type == 'math':
                return self._grade_math(detected_text, contours, answer_key)
            elif self.subject_type == 'english':
                return self._grade_english(detected_text, contours, answer_key)
            else:
                return self._grade_generic(detected_text, contours, answer_key)
                
        except Exception as e:
            self._log_processing(f"Answer matching failed: {str(e)}")
            raise
    
    def _grade_math(self, text, contours, answer_key):
        """Specialized math answer grading"""
        # Implement math-specific logic (show work, partial credit, etc.)
        self._log_processing("Using math grading rubric")
        
        # Example: Extract multiple choice answers
        answers = re.findall(r'Q\d+:\s*([A-D])', text)
        key_answers = re.findall(r'Q\d+:\s*([A-D])', answer_key)
        
        score = sum(1 for a, k in zip(answers, key_answers) if a == k) / len(key_answers) * 100
        return {
            'score': round(score, 2),
            'details': f"Math answers matched: {len(answers)}/{len(key_answers)}",
            'feedback': self._generate_math_feedback(answers, key_answers)
        }
    
    def _grade_english(self, text, contours, answer_key):
        """Specialized English answer grading"""
        self._log_processing("Using English grading rubric")
        
        # Implement essay scoring or language-specific grading
        return {
            'score': self._score_essay(text, answer_key),
            'details': "English composition evaluated",
            'feedback': self._generate_english_feedback(text)
        }
    
    def _grade_generic(self, text, contours, answer_key):
        """Default grading for other subjects"""
        self._log_processing("Using generic grading rubric")
        
        # Basic multiple choice matching
        answers = re.findall(r'[A-D]', text.upper())
        key_answers = re.findall(r'[A-D]', answer_key.upper())
        
        correct = sum(1 for a, k in zip(answers, key_answers) if a == k)
        score = (correct / len(key_answers)) * 100 if key_answers else 0
        
        return {
            'score': round(score, 2),
            'details': f"Correct answers: {correct}/{len(key_answers)}",
            'feedback': ""
        }
    
    def action_grade_script(self):
        """Complete grading workflow"""
        for script in self:
            try:
                script._log_processing("Starting grading process")
                
                # 1. Process uploaded script
                file_data = base64.b64decode(script.script_file)
                if script.file_type == 'pdf':
                    text, contours = script._extract_from_pdf(file_data)
                else:
                    text, contours = script._extract_from_image(file_data)
                
                # 2. Process answer key
                answer_key = script._parse_answer_key()
                
                # 3. Grade according to subject
                results = script._match_answers(text, contours, answer_key)
                
                # 4. Save results
                script.write({
                    'ai_score': results['score'],
                    'detected_answers': results['details'],
                    'scoring_complete': True,
                })
                
                script._log_processing(f"Grading completed. Score: {results['score']}")
                
            except Exception as e:
                script._log_processing(f"Grading failed: {str(e)}")
                raise UserError(_("Grading failed. See processing log for details."))                
    
    @api.model
    def _check_dependencies(self):
        if not DEPENDENCIES_INSTALLED:
            raise UserError(_(
                "Required Python packages not installed. Please install with:\n\n"
                "pip install pytesseract opencv-python pymupdf numpy pillow"
            ))
        
        # Verify Tesseract is installed
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            raise UserError(_(
                "Tesseract OCR not found. Please install:\n\n"
                "Linux: sudo apt install tesseract-ocr\n"
                "MacOS: brew install tesseract"
            ))

    def action_grade_script(self):
        """Override with dependency check"""
        self._check_dependencies()
        return super().action_grade_script()                
