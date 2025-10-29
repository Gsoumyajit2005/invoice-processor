import os
import json
import glob
from datetime import datetime
import cv2
import pytesseract

# Import our existing functions
from extract_fields_v3 import (
    extract_receipt_fields_v3,
    validate_extraction,
    calculate_confidence_score
)

def process_single_invoice(image_path, output_dir):
    """
    Complete pipeline for one invoice: OCR → Extract → Validate → Save
    
    Args:
        image_path: Path to invoice image
        output_dir: Where to save results
    
    Returns:
        Dictionary with results and metadata
    """
    filename = os.path.basename(image_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    print(f"\n{'='*70}")
    print(f"📄 Processing: {filename}")
    print(f"{'='*70}")
    
    result = {
        'filename': filename,
        'status': 'success',
        'data': None,
        'error': None,
        'processing_time': 0
    }
    
    start_time = datetime.now()
    
    try:
        # Step 1: OCR
        print("🔍 Running OCR...")
        img = cv2.imread(image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        ocr_text = pytesseract.image_to_string(img_rgb)
        
        # Save OCR text
        ocr_output_path = os.path.join(output_dir, f"{name_without_ext}_ocr.txt")
        with open(ocr_output_path, 'w', encoding='utf-8') as f:
            f.write(ocr_text)
        print(f"   💾 OCR text saved to: {ocr_output_path}")
        
        # Step 2: Extract structured data
        print("\n🔧 Extracting structured data...")
        extracted_data = extract_receipt_fields_v3(ocr_text)
        
        # Step 3: Validate
        print("\n🔎 Validating...")
        warnings = validate_extraction(extracted_data)
        
        # Step 4: Calculate confidence
        confidence = calculate_confidence_score(extracted_data)
        extracted_data['extraction_confidence'] = confidence
        extracted_data['validation_warnings'] = warnings
        extracted_data['source_file'] = filename
        extracted_data['processed_at'] = datetime.now().isoformat()
        
        # Step 5: Save JSON
        json_output_path = os.path.join(output_dir, f"{name_without_ext}_structured.json")
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Structured data saved to: {json_output_path}")
        
        # Update result
        result['data'] = extracted_data
        result['status'] = 'success' if not warnings else 'success_with_warnings'
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        result['status'] = 'failed'
        result['error'] = str(e)
    
    end_time = datetime.now()
    result['processing_time'] = (end_time - start_time).total_seconds()
    
    print(f"\n⏱️ Processing time: {result['processing_time']:.2f} seconds")
    print(f"✅ Status: {result['status']}")
    
    return result


def process_all_invoices(input_dir, output_dir):
    """
    Process all invoice images in a directory.
    
    Args:
        input_dir: Folder with invoice images
        output_dir: Where to save results
    """
    # Find all images
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.PNG']
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(input_dir, ext)))
    
    if not image_files:
        print(f"❌ No images found in {input_dir}")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print("="*70)
    print("🚀 BATCH INVOICE PROCESSING")
    print("="*70)
    print(f"📁 Input directory: {input_dir}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📊 Found {len(image_files)} invoice(s)")
    print("="*70)
    
    # Process each invoice
    results = []
    for idx, image_path in enumerate(image_files, 1):
        print(f"\n[{idx}/{len(image_files)}]")
        result = process_single_invoice(image_path, output_dir)
        results.append(result)
    
    # Generate summary report
    generate_summary_report(results, output_dir)


def generate_summary_report(results, output_dir):
    """
    Create a summary report of all processed invoices.
    
    Args:
        results: List of processing results
        output_dir: Where to save report
    """
    print("\n" + "="*70)
    print("📊 BATCH PROCESSING SUMMARY")
    print("="*70)
    
    # Count statuses
    success_count = sum(1 for r in results if r['status'] == 'success')
    warning_count = sum(1 for r in results if r['status'] == 'success_with_warnings')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    
    print(f"\n✅ Successful: {success_count}")
    print(f"⚠️ With warnings: {warning_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Total: {len(results)}")
    
    # Detailed table
    print(f"\n{'Filename':<25} {'Status':<20} {'Confidence':<12} {'Time':<8}")
    print("-"*70)
    
    for r in results:
        status_icon = {
            'success': '✅',
            'success_with_warnings': '⚠️',
            'failed': '❌'
        }.get(r['status'], '❓')
        
        confidence = r['data']['extraction_confidence'] if r['data'] else 0
        
        print(f"{r['filename']:<25} {status_icon} {r['status']:<18} {confidence:>3.0f}% {' '*7} {r['processing_time']:>5.2f}s")
    
    # Calculate totals
    avg_time = sum(r['processing_time'] for r in results) / len(results)
    total_amount = sum(
        r['data']['total_amount'] 
        for r in results 
        if r['data'] and r['data'].get('total_amount')
    )
    
    print("-"*70)
    print(f"Average processing time: {avg_time:.2f}s")
    print(f"Total amount across all invoices: ${total_amount:.2f}")
    
    # Save summary as JSON
    summary = {
        'processed_at': datetime.now().isoformat(),
        'total_invoices': len(results),
        'successful': success_count,
        'with_warnings': warning_count,
        'failed': failed_count,
        'average_processing_time': avg_time,
        'total_amount_sum': total_amount,
        'details': [
            {
                'filename': r['filename'],
                'status': r['status'],
                'confidence': r['data']['extraction_confidence'] if r['data'] else 0,
                'total_amount': r['data'].get('total_amount') if r['data'] else None,
                'processing_time': r['processing_time'],
                'warnings': r['data'].get('validation_warnings', []) if r['data'] else [],
                'error': r['error']
            }
            for r in results
        ]
    }
    
    summary_path = os.path.join(output_dir, '_batch_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Summary report saved to: {summary_path}")
    print("="*70)


if __name__ == "__main__":
    # Process all invoices in data/raw/
    input_directory = "data/raw"
    output_directory = "data/processed/batch_results"
    
    process_all_invoices(input_directory, output_directory)
    
    print("\n🎉 Batch processing complete!")
    print(f"📁 Check {output_directory} for all results")