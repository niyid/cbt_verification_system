#!/bin/bash

# Install system dependencies
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr libtesseract-dev libleptonica-dev
    sudo apt-get install -y python3-opencv
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew install tesseract
    brew install leptonica
fi

# Install Python packages through pip
pip install --upgrade pip
pip install pytesseract opencv-python pymupdf numpy Pillow
