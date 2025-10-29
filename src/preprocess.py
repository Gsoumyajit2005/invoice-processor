from PIL import Image
import cv2
import numpy as np
import os

def preprocess_invoice(image_path, output_path=None):
    """
    Preprocesses an invoice image for better OCR results.
    
    Steps:
    1. Load image
    2. Convert RGBA to RGB (remove transparency)
    3. Convert to grayscale
    4. Enhance contrast
    5. Save processed image
    
    Args:
        image_path: Path to input image
        output_path: Where to save processed image (optional)
    
    Returns:
        Processed image as numpy array
    """
    
    print(f"📂 Loading image from: {image_path}")
    
    # Step 1: Load with PIL first
    img_pil = Image.open(image_path)
    print(f"📐 Original size: {img_pil.size}, Mode: {img_pil.mode}")
    
    # Step 2: Convert RGBA to RGB if needed
    if img_pil.mode == 'RGBA':
        print("🔄 Converting RGBA to RGB...")
        # Create a white background
        rgb_img = Image.new('RGB', img_pil.size, (255, 255, 255))
        # Paste the image on white background
        rgb_img.paste(img_pil, mask=img_pil.split()[3])  # Use alpha channel as mask
        img_pil = rgb_img
    elif img_pil.mode != 'RGB':
        print(f"🔄 Converting {img_pil.mode} to RGB...")
        img_pil = img_pil.convert('RGB')
    
    # Step 3: Convert PIL to numpy array (OpenCV format)
    img_np = np.array(img_pil)
    # PIL uses RGB, OpenCV uses BGR, so convert
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # Step 4: Convert to grayscale
    print("⚫ Converting to grayscale...")
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Step 5: Enhance contrast using CLAHE
    # (Contrast Limited Adaptive Histogram Equalization)
    print("✨ Enhancing contrast...")
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Step 6: Denoise (remove small specks/noise)
    print("🧹 Removing noise...")
    denoised = cv2.fastNlMeansDenoising(enhanced, h=20)
    
    print("✅ Preprocessing complete!")
    
    # Step 7: Save if output path provided
    if output_path:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, denoised)
        print(f"💾 Saved processed image to: {output_path}")
    
    return denoised


def show_comparison(original_path, processed_image):
    """
    Show original vs processed image side by side.
    Also saves separate before/after images.
    
    Args:
        original_path: Path to original image
        processed_image: Processed image (numpy array)
    """
    # Load original - KEEP IT IN COLOR
    original = cv2.imread(original_path)
    
    # Resize both to same height for comparison
    height = 800
    original_resized = resize_image(original, height)
    processed_resized = resize_image(processed_image, height)
    
    # Convert processed back to BGR so we can stack them
    # (processed is grayscale, original is color BGR)
    processed_bgr = cv2.cvtColor(processed_resized, cv2.COLOR_GRAY2BGR)
    
    # Stack side by side
    comparison = np.hstack([original_resized, processed_bgr])
    
    # Add labels
    comparison_labeled = comparison.copy()
    cv2.putText(comparison_labeled, 'ORIGINAL (Color)', (10, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(comparison_labeled, 'PROCESSED (Grayscale + Enhanced)', 
                (original_resized.shape[1] + 10, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Save comparison
    cv2.imwrite('data/processed/comparison.jpg', comparison_labeled)
    print("💾 Saved comparison to: data/processed/comparison.jpg")
    
    # Display
    cv2.imshow('Comparison (Press any key to close)', comparison_labeled)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def resize_image(image, target_height):
    """
    Resize image maintaining aspect ratio.
    
    Args:
        image: Input image
        target_height: Desired height
    
    Returns:
        Resized image
    """
    height, width = image.shape[:2]
    ratio = target_height / height
    new_width = int(width * ratio)
    return cv2.resize(image, (new_width, target_height))


def detailed_comparison(original_path, processed_image):
    """
    Create a detailed before/after comparison with zoomed sections.
    This helps see the actual differences.
    
    Args:
        original_path: Path to original image
        processed_image: Processed image (numpy array)
    """
    # Load original
    original = cv2.imread(original_path)
    original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    
    # Calculate and show statistics
    print("\n📊 IMAGE STATISTICS:")
    print(f"Original - Mean brightness: {original_gray.mean():.2f}, Std: {original_gray.std():.2f}")
    print(f"Processed - Mean brightness: {processed_image.mean():.2f}, Std: {processed_image.std():.2f}")
    
    # Higher std = more contrast (bigger difference between dark and light)
    contrast_improvement = ((processed_image.std() - original_gray.std()) / original_gray.std()) * 100
    print(f"✨ Contrast improvement: {contrast_improvement:.2f}%")
    
    # Save individual images for manual inspection
    cv2.imwrite('data/processed/original_gray.jpg', original_gray)
    cv2.imwrite('data/processed/enhanced.jpg', processed_image)
    print("\n💾 Saved individual images:")
    print("   - data/processed/original_gray.jpg")
    print("   - data/processed/enhanced.jpg")
    
    # Create a difference map (shows what changed)
    difference = cv2.absdiff(original_gray, processed_image)
    
    # Amplify differences so they're visible
    difference_amplified = cv2.multiply(difference, np.array([5.0]))
    
    cv2.imwrite('data/processed/difference_map.jpg', difference_amplified)
    print("   - data/processed/difference_map.jpg (what changed - brighter = more change)")
    
    # Show zoomed crop (top portion where header usually is)
    h, w = original_gray.shape
    crop_region = (slice(0, h//4), slice(0, w//2))  # Top-left quarter
    
    original_crop = original_gray[crop_region]
    processed_crop = processed_image[crop_region]
    
    # Resize crops for viewing
    zoom_factor = 2
    original_zoom = cv2.resize(original_crop, None, fx=zoom_factor, fy=zoom_factor)
    processed_zoom = cv2.resize(processed_crop, None, fx=zoom_factor, fy=zoom_factor)
    
    # Convert to BGR for stacking
    original_zoom_bgr = cv2.cvtColor(original_zoom, cv2.COLOR_GRAY2BGR)
    processed_zoom_bgr = cv2.cvtColor(processed_zoom, cv2.COLOR_GRAY2BGR)
    
    zoom_comparison = np.hstack([original_zoom_bgr, processed_zoom_bgr])
    
    cv2.imwrite('data/processed/zoomed_comparison.jpg', zoom_comparison)
    print("   - data/processed/zoomed_comparison.jpg (zoomed-in comparison)")
    
    print("\n👁️ Open these files to see the differences clearly!")


if __name__ == "__main__":
    # Test the preprocessing
    input_path = "data/raw/invoice_2.jpg"
    output_path = "data/processed/invoice_1_processed.png"
    
    print("="*60)
    print("🚀 INVOICE PREPROCESSING")
    print("="*60)
    
    # Process the image
    processed = preprocess_invoice(input_path, output_path)
    
    print("\n" + "="*60)
    # Show comparison window
    print("\n👁️ Displaying comparison window...")
    show_comparison(input_path, processed)
    
    print("\n" + "="*60)
    # Create detailed comparison
    detailed_comparison(input_path, processed)
    
    print("\n" + "="*60)
    print("✅ ALL DONE! Check the data/processed/ folder")
    print("="*60)