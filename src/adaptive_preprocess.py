from PIL import Image
import cv2
import numpy as np
import os

def analyze_image_quality(image_path):
    """
    Analyze image to determine if preprocessing is needed.
    
    Returns:
        dict with quality metrics
    """
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Calculate metrics
    metrics = {
        'mean_brightness': gray.mean(),
        'contrast': gray.std(),
        'sharpness': cv2.Laplacian(gray, cv2.CV_64F).var(),
        'size': gray.shape
    }
    
    return metrics


def should_preprocess(metrics):
    """
    Decide if image needs preprocessing based on quality metrics.
    
    Args:
        metrics: Dictionary from analyze_image_quality()
    
    Returns:
        dict: What preprocessing steps to apply
    """
    needs = {
        'contrast_enhancement': False,
        'denoising': False,
        'reason': []
    }
    
    # Check contrast (std < 40 means low contrast)
    if metrics['contrast'] < 40:
        needs['contrast_enhancement'] = True
        needs['reason'].append(f"Low contrast ({metrics['contrast']:.1f})")
    
    # Check if image is too dark or too bright
    if metrics['mean_brightness'] < 80 or metrics['mean_brightness'] > 200:
        needs['contrast_enhancement'] = True
        needs['reason'].append(f"Poor brightness ({metrics['mean_brightness']:.1f})")
    
    # Check sharpness (< 100 means blurry)
    if metrics['sharpness'] < 100:
        needs['denoising'] = False  # Don't denoise blurry images (makes worse)
        needs['reason'].append(f"Image is blurry ({metrics['sharpness']:.1f})")
    elif metrics['sharpness'] < 500:
        needs['denoising'] = True
        needs['reason'].append(f"Some noise detected ({metrics['sharpness']:.1f})")
    
    return needs


def smart_preprocess(image_path, output_path=None):
    """
    Intelligently preprocess based on image quality.
    Only applies steps that will help.
    
    Args:
        image_path: Path to input image
        output_path: Where to save (optional)
    
    Returns:
        Processed image as numpy array
    """
    print(f"📂 Loading: {image_path}\n")
    
    # Analyze first
    metrics = analyze_image_quality(image_path)
    print("📊 IMAGE QUALITY ANALYSIS:")
    print(f"   Brightness: {metrics['mean_brightness']:.1f} (good: 80-200)")
    print(f"   Contrast: {metrics['contrast']:.1f} (good: >40)")
    print(f"   Sharpness: {metrics['sharpness']:.1f} (good: >100)")
    print(f"   Size: {metrics['size'][1]}x{metrics['size'][0]} pixels\n")
    
    # Decide what to do
    needs = should_preprocess(metrics)
    
    if not needs['contrast_enhancement'] and not needs['denoising']:
        print("✅ IMAGE QUALITY IS GOOD!")
        print("📋 Recommendation: Use original image (minimal processing)\n")
    else:
        print("⚠️ IMAGE NEEDS IMPROVEMENT:")
        for reason in needs['reason']:
            print(f"   - {reason}")
        print()
    
    # Load image
    img = cv2.imread(image_path)
    
    # Always convert to grayscale (OCR doesn't need color)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    processed = gray.copy()
    
    steps_applied = []
    
    # Apply contrast enhancement only if needed
    if needs['contrast_enhancement']:
        print("🔧 Applying contrast enhancement...")
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        processed = clahe.apply(processed)
        steps_applied.append("Contrast Enhancement")
    
    # Apply denoising only if needed
    if needs['denoising']:
        print("🔧 Applying denoising...")
        processed = cv2.fastNlMeansDenoising(processed, h=10)
        steps_applied.append("Denoising")
    
    if not steps_applied:
        print("🔧 Converting to grayscale only (no enhancement needed)")
        steps_applied.append("Grayscale conversion")
    
    # Calculate actual improvement
    original_contrast = gray.std()
    new_contrast = processed.std()
    improvement = ((new_contrast - original_contrast) / original_contrast) * 100
    
    print(f"\n📈 RESULTS:")
    print(f"   Steps applied: {', '.join(steps_applied)}")
    print(f"   Contrast change: {improvement:+.2f}%")
    
    if improvement < 0:
        print("   ⚠️ Negative improvement - using minimal processing!")
        processed = gray  # Use just grayscale, no enhancement
    
    # Save
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, processed)
        print(f"   💾 Saved to: {output_path}")
    
    return processed, metrics, improvement


def process_multiple_invoices(input_dir, output_dir):
    """
    Process all images in a directory with smart preprocessing.
    
    Args:
        input_dir: Folder with invoice images
        output_dir: Where to save processed images
    """
    import glob
    
    image_files = glob.glob(f"{input_dir}/*.jpg") + glob.glob(f"{input_dir}/*.png")
    
    print("="*70)
    print(f"📁 Found {len(image_files)} images in {input_dir}")
    print("="*70 + "\n")
    
    results = []
    
    for idx, img_path in enumerate(image_files, 1):
        filename = os.path.basename(img_path)
        output_path = os.path.join(output_dir, f"processed_{filename}")
        
        print(f"[{idx}/{len(image_files)}] Processing: {filename}")
        print("-" * 70)
        
        processed, metrics, improvement = smart_preprocess(img_path, output_path)
        
        results.append({
            'filename': filename,
            'brightness': metrics['mean_brightness'],
            'contrast': metrics['contrast'],
            'sharpness': metrics['sharpness'],
            'improvement': improvement
        })
        
        print("\n")
    
    # Summary
    print("="*70)
    print("📊 PROCESSING SUMMARY")
    print("="*70)
    print(f"{'Filename':<20} {'Brightness':<12} {'Contrast':<10} {'Improvement':<12}")
    print("-"*70)
    for r in results:
        print(f"{r['filename']:<20} {r['brightness']:<12.1f} {r['contrast']:<10.1f} {r['improvement']:+.2f}%")
    
    avg_improvement = sum(r['improvement'] for r in results) / len(results)
    print("-"*70)
    print(f"Average improvement: {avg_improvement:+.2f}%")
    print("="*70)


if __name__ == "__main__":
    # Process all invoices in data/raw/
    process_multiple_invoices("data/raw", "data/processed")