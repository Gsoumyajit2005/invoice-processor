import cv2
import os

def prepare_for_ocr(image_path, output_path=None):
    """
    Minimal preprocessing for high-quality invoice images.
    Just converts to grayscale - perfect for clean photos.
    
    Args:
        image_path: Path to input image
        output_path: Where to save (optional)
    
    Returns:
        Grayscale image ready for OCR
    """
    print(f"📂 Loading: {image_path}")
    
    # Load image
    img = cv2.imread(image_path)
    
    # Convert to grayscale (OCR works best on grayscale)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    print(f"✅ Converted to grayscale: {gray.shape[1]}x{gray.shape[0]} pixels")
    
    # Save if requested
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, gray)
        print(f"💾 Saved to: {output_path}")
    
    return gray


if __name__ == "__main__":
    # Process your invoices with minimal preprocessing
    import glob
    
    image_files = glob.glob("data/raw/*.jpg") + glob.glob("data/raw/*.png")
    
    print("="*60)
    print("🚀 PREPARING IMAGES FOR OCR (Minimal Processing)")
    print("="*60 + "\n")
    
    for img_path in image_files:
        filename = os.path.basename(img_path)
        name, ext = os.path.splitext(filename)
        output_path = f"data/processed/{name}_ocr_ready.jpg"
        
        prepare_for_ocr(img_path, output_path)
        print()
    
    print("="*60)
    print("✅ All images ready for OCR!")
    print("="*60)