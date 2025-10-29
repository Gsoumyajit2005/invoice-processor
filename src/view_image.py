from PIL import Image
import sys
from pathlib import Path

def view_invoice(image_path):
    """
    Opens and displays an invoice image.

    Args:
        image_path: Path to the invoice image file
    """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Print basic info
        print(f"✅ Image loaded successfully!")
        print(f"📄 File: {image_path}")
        print(f"📐 Size: {img.size}")  # (width, height)
        print(f"🎨 Mode: {img.mode}")  # RGB, RGBA, L (grayscale), etc.
        
        # Display the image
        img.show()
        
    except FileNotFoundError:
        print(f"❌ Error: File not found at {image_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Test with your invoice
    view_invoice("data/raw/invoice_1.png")