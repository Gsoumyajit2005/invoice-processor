# Quick Start Guide

## Installation (5 minutes)

### 1. Install Tesseract OCR

**Windows:**
1. Download: [Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run installer
3. Add to PATH: `C:\Program Files\Tesseract-OCR`

**Mac:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt update
sudo apt install tesseract-ocr
```

### 2. Install Python Dependencies

# Clone repository
git clone https://github.com/yourusername/invoice-processor
cd invoice-processor

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

### 3. Run the App

```bash
streamlit run app.py
```