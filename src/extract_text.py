import pytesseract
import cv2
import os

# If on Windows and tesseract not in PATH, uncomment and set this:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path):
    """
    Extract all text from an invoice image using OCR.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Extracted text as string
    """
    print(f"📂 Reading: {image_path}")
    
    # Load image
    img = cv2.imread(image_path)
    
    # Convert to RGB (Tesseract expects RGB, OpenCV loads as BGR)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    print("🔍 Running OCR (this may take a few seconds)...")
    
    # Extract text
    text = pytesseract.image_to_string(img_rgb)
    
    print(f"✅ Extracted {len(text)} characters\n")
    
    return text


def extract_with_confidence(image_path):
    """
    Extract text with confidence scores for each word.
    This helps identify which parts OCR is uncertain about.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Dictionary with detailed OCR data
    """
    print(f"📂 Reading: {image_path}")
    
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    print("🔍 Running detailed OCR...")
    
    # Get detailed data (word-level with bounding boxes and confidence)
    data = pytesseract.image_to_data(img_rgb, output_type=pytesseract.Output.DICT)
    
    # Filter out empty detections
    n_boxes = len(data['text'])
    words_with_confidence = []
    
    for i in range(n_boxes):
        text = data['text'][i].strip()
        conf = int(data['conf'][i])
        
        if text and conf > 0:  # Only keep actual words with confidence
            words_with_confidence.append({
                'text': text,
                'confidence': conf,
                'x': data['left'][i],
                'y': data['top'][i],
                'width': data['width'][i],
                'height': data['height'][i]
            })
    
    print(f"✅ Found {len(words_with_confidence)} words\n")
    
    return words_with_confidence


if __name__ == "__main__":
    # Test with your processed invoice
    test_image = "data/processed/invoice_1_ocr_ready.jpg"
    
    # Check if file exists
    if not os.path.exists(test_image):
        print(f"❌ File not found: {test_image}")
        print("Run simple_preprocess.py first!")
        exit()
    
    print("="*70)
    print("🚀 TESSERACT OCR TEST")
    print("="*70 + "\n")
    
    # Method 1: Simple text extraction
    print("METHOD 1: Simple Text Extraction")
    print("-"*70)
    text = extract_text_from_image(test_image)
    print("EXTRACTED TEXT:")
    print("="*70)
    print(text)
    print("="*70 + "\n")
    
    # Method 2: With confidence scores
    print("METHOD 2: Detailed Extraction (with confidence)")
    print("-"*70)
    words = extract_with_confidence(test_image)
    
    # Show first 20 words with confidence
    print("\nFirst 20 detected words:")
    print(f"{'Word':<30} {'Confidence':<12}")
    print("-"*50)
    for word in words[:20]:
        conf_bar = "█" * (word['confidence'] // 10)  # Visual confidence bar
        print(f"{word['text']:<30} {word['confidence']:>3}% {conf_bar}")
    
    # Calculate average confidence
    avg_conf = sum(w['confidence'] for w in words) / len(words) if words else 0
    print("-"*50)
    print(f"Average confidence: {avg_conf:.1f}%")
    
    # Save to file
    output_file = "data/processed/extracted_text.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"\n💾 Saved full text to: {output_file}")