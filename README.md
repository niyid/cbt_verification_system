# CBT Verification System Module

## Installation

1. Install system dependencies:
```bash
sudo apt install tesseract-ocr libtesseract-dev libleptonica-dev
```

2. Install Python packages:
```bash
pip install pytesseract opencv-python pymupdf numpy pillow
```

3. Install the module in Odoo:
- Go to Apps → Update Apps List
- Click "Install" on CBT Verification System

## Configuration

1. Set DeepSeek API key:
- Go to Settings → General Settings → DeepSeek Configuration
- Enter your API key

2. Configure grading parameters:
- Each test script can have subject-specific grading rules

## Usage

1. Applicants can:
- File complaints via portal
- Upload supporting documents
- Track complaint status

2. Administrators can:
- Process answer sheets
- View AI grading results
- Manage verification workflow
