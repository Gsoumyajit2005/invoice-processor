import re
import json
from datetime import datetime

def extract_receipt_fields(text):
    """
    Extract structured information from OCR text.
    Uses regex patterns to find specific fields.
    
    Args:
        text: Raw OCR text
    
    Returns:
        Dictionary with extracted fields
    """
    
    data = {
        "receipt_number": None,
        "date": None,
        "bill_to": {
            "name": None,
            "email": None
        },
        "items": [],
        "total_amount": None,
        "payment_method": None
    }
    
    print("🔍 Extracting structured data...\n")
    
    # 1. Extract Receipt Number
    # Pattern: "Receipt #" followed by digits
    receipt_pattern = r'Receipt\s*#(\d+)'
    receipt_match = re.search(receipt_pattern, text, re.IGNORECASE)
    if receipt_match:
        data['receipt_number'] = receipt_match.group(1)
        print(f"✅ Receipt Number: {data['receipt_number']}")
    else:
        print("❌ Receipt Number: Not found")
    
    # 2. Extract Date
    # Pattern: Month Day, Year (e.g., "March 15, 2050")
    date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})'
    date_match = re.search(date_pattern, text)
    if date_match:
        data['date'] = f"{date_match.group(1)} {date_match.group(2)}, {date_match.group(3)}"
        print(f"✅ Date: {data['date']}")
    else:
        print("❌ Date: Not found")
    
    # 3. Extract Bill To Information
    # Pattern: "Bill To:" followed by name on next section, then email
    bill_to_pattern = r'Bill\s+To:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    bill_match = re.search(bill_to_pattern, text)
    if bill_match:
        data['bill_to']['name'] = bill_match.group(1)
        data['bill_to']['email'] = bill_match.group(2)
        print(f"✅ Bill To: {data['bill_to']['name']} ({data['bill_to']['email']})")
    else:
        print("❌ Bill To: Not found")
    
    # 4. Extract Total Amount
    # Pattern: "Total Amount:" followed by dollar amount
    total_pattern = r'Total\s+Amount:\s*\$?([\d,]+\.?\d*)'
    total_match = re.search(total_pattern, text, re.IGNORECASE)
    if total_match:
        # Remove commas and convert to float
        amount_str = total_match.group(1).replace(',', '')
        data['total_amount'] = float(amount_str)
        print(f"✅ Total Amount: ${data['total_amount']:.2f}")
    else:
        print("❌ Total Amount: Not found")
    
    # 5. Extract Payment Method
    # Pattern: "Payment Method:" followed by the method
    payment_pattern = r'Payment\s+Method:\s*([A-Za-z\s]+)'
    payment_match = re.search(payment_pattern, text, re.IGNORECASE)
    if payment_match:
        data['payment_method'] = payment_match.group(1).strip()
        print(f"✅ Payment Method: {data['payment_method']}")
    else:
        print("❌ Payment Method: Not found")
    
    # 6. Extract Line Items (This is trickier!)
    # Pattern: Item description, quantity, unit price, total
    # We'll look for lines with this pattern
    item_pattern = r'([A-Za-z\s]+?)\s+(\d+)\s+\$(\d+\.\d{2})\s+\$(\d+\.\d{2})'
    items = re.findall(item_pattern, text)
    
    print(f"\n📦 Line Items Found: {len(items)}")
    for idx, item in enumerate(items, 1):
        item_data = {
            "description": item[0].strip(),
            "quantity": int(item[1]),
            "unit_price": float(item[2]),
            "total": float(item[3])
        }
        data['items'].append(item_data)
        print(f"   {idx}. {item_data['description']} - Qty: {item_data['quantity']} - Total: ${item_data['total']:.2f}")
    
    return data


def calculate_confidence_score(data):
    """
    Calculate how confident we are in the extraction.
    Based on which fields were successfully extracted.
    
    Args:
        data: Extracted data dictionary
    
    Returns:
        Confidence score (0-100)
    """
    fields_to_check = [
        ('receipt_number', 20),  # Each field has a weight
        ('date', 20),
        ('bill_to.name', 15),
        ('bill_to.email', 15),
        ('total_amount', 20),
        ('payment_method', 10)
    ]
    
    score = 0
    
    for field_path, weight in fields_to_check:
        # Navigate nested fields (e.g., "bill_to.name")
        value = data
        for key in field_path.split('.'):
            value = value.get(key) if isinstance(value, dict) else None
        
        if value:
            score += weight
    
    # Bonus points for items
    if data['items']:
        score += min(len(data['items']) * 2.5, 10)  # Up to 10 points for items
    
    return min(score, 100)  # Cap at 100


def save_to_json(data, output_path):
    """
    Save extracted data as formatted JSON.
    
    Args:
        data: Dictionary to save
        output_path: Where to save
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved structured data to: {output_path}")


if __name__ == "__main__":
    # Load the OCR text
    text_file = "data/processed/extracted_text.txt"
    
    print("="*70)
    print("🚀 STRUCTURED DATA EXTRACTION")
    print("="*70 + "\n")
    
    # Read text
    with open(text_file, 'r', encoding='utf-8') as f:
        ocr_text = f.read()
    
    # Extract fields
    extracted_data = extract_receipt_fields(ocr_text)
    
    # Calculate confidence
    confidence = calculate_confidence_score(extracted_data)
    extracted_data['extraction_confidence'] = confidence
    
    print("\n" + "="*70)
    print(f"📊 Extraction Confidence: {confidence:.0f}%")
    print("="*70)
    
    # Display as JSON
    print("\n📄 STRUCTURED OUTPUT (JSON):")
    print("="*70)
    print(json.dumps(extracted_data, indent=2))
    print("="*70)
    
    # Save to file
    output_file = "data/processed/invoice_1_structured.json"
    save_to_json(extracted_data, output_file)
    
    print("\n✅ Extraction complete!")