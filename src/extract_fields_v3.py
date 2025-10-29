import re
import json

def normalize_ocr_errors(text):
    """
    Fix common OCR character recognition errors.
    
    Common mistakes:
    - 'J' or 'l' or 'I' instead of '1' in quantity fields
    - 'O' instead of '0' in numbers
    - 'S' instead of '5'
    
    Args:
        text: OCR text with potential errors
    
    Returns:
        Corrected text
    """
    lines = text.split('\n')
    corrected_lines = []
    
    for line in lines:
        # If line looks like an item (has $ signs), try to fix quantity
        if '$' in line and not line.startswith('Total'):
            # Pattern: text followed by single letter that might be a number
            # Example: "Premium Software Subscription J $150.00 $150.00"
            
            # Look for single character before first dollar sign that might be misread '1'
            fixed_line = re.sub(
                r'\s+([JlI])\s+\$',  # Single J, l, or I before $
                r' 1 $',             # Replace with 1
                line
            )
            
            # Fix O to 0 in prices (but be careful - could be letter O in description)
            # Only in the number parts (after $)
            parts = fixed_line.split('$')
            if len(parts) > 1:
                # First part is description, keep as is
                # Rest are prices, fix O to 0
                parts[1:] = [p.replace('O', '0') for p in parts[1:]]
                fixed_line = '$'.join(parts)
            
            corrected_lines.append(fixed_line)
        else:
            corrected_lines.append(line)
    
    return '\n'.join(corrected_lines)


def extract_receipt_fields_v3(text):
    """
    Improved extraction with OCR error correction.
    
    Args:
        text: Raw OCR text
    
    Returns:
        Dictionary with extracted fields
    """
    
    # STEP 0: Fix common OCR errors FIRST
    print("🔧 Correcting common OCR errors...")
    corrected_text = normalize_ocr_errors(text)
    
    data = {
        "receipt_number": None,
        "date": None,
        "bill_to": {
            "name": None,
            "email": None
        },
        "items": [],
        "total_amount": None,
        "payment_method": None,
        "ocr_corrections_applied": True
    }
    
    print("🔍 Extracting structured data (v3 - with OCR correction)...\n")
    
    # Use corrected text for extraction
    text = corrected_text
    
    # 1. Extract Receipt Number
    receipt_pattern = r'Receipt\s*#(\d+)'
    receipt_match = re.search(receipt_pattern, text, re.IGNORECASE)
    if receipt_match:
        data['receipt_number'] = receipt_match.group(1)
        print(f"✅ Receipt Number: {data['receipt_number']}")
    else:
        print("❌ Receipt Number: Not found")
    
    # 2. Extract Date
    date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})'
    date_match = re.search(date_pattern, text)
    if date_match:
        data['date'] = f"{date_match.group(1)} {date_match.group(2)}, {date_match.group(3)}"
        print(f"✅ Date: {data['date']}")
    else:
        print("❌ Date: Not found")
    
    # 3. Extract Bill To - Name
    name_pattern = r'Bill\s+To:\s*\n?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
    name_match = re.search(name_pattern, text)
    if name_match:
        data['bill_to']['name'] = name_match.group(1).strip()
        print(f"✅ Bill To Name: {data['bill_to']['name']}")
    else:
        print("❌ Bill To Name: Not found")
    
    # Extract email separately
    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    email_matches = re.findall(email_pattern, text)
    for email in email_matches:
        if not email.startswith('inquire'):
            data['bill_to']['email'] = email
            print(f"✅ Bill To Email: {data['bill_to']['email']}")
            break
    
    # 4. Extract Total Amount
    total_pattern = r'Total\s+Amount:\s*\$?([\d,]+\.?\d*)'
    total_match = re.search(total_pattern, text, re.IGNORECASE)
    if total_match:
        amount_str = total_match.group(1).replace(',', '')
        data['total_amount'] = float(amount_str)
        print(f"✅ Total Amount: ${data['total_amount']:.2f}")
    else:
        print("❌ Total Amount: Not found")
    
    # 5. Extract Payment Method
    payment_pattern = r'Payment\s+Method:\s*([^\n]+)'
    payment_match = re.search(payment_pattern, text, re.IGNORECASE)
    if payment_match:
        data['payment_method'] = payment_match.group(1).strip()
        print(f"✅ Payment Method: {data['payment_method']}")
    else:
        print("❌ Payment Method: Not found")
    
    # 6. Extract Line Items
    print(f"\n📦 Extracting line items...")
    data['items'] = extract_line_items(text)
    
    return data


def extract_line_items(text):
    """
    Extract line items with better error handling.
    """
    items = []
    
    lines = text.split('\n')
    
    # Find table boundaries
    table_start = -1
    table_end = -1
    
    for i, line in enumerate(lines):
        if 'Item Description' in line and 'Quantity' in line:
            table_start = i + 1
        if 'Total Amount:' in line:
            table_end = i
            break
    
    if table_start == -1:
        print("   ⚠️ Could not find item table header")
        return items
    
    print(f"   📍 Found table between lines {table_start} and {table_end}")
    
    # Extract items
    for i in range(table_start, table_end if table_end != -1 else len(lines)):
        line = lines[i].strip()
        
        if not line:
            continue
        
        # Pattern: Description, quantity (now allowing 1), unit price, total
        item_pattern = r'^(.+?)\s+(\d+)\s+\$?(\d+\.\d{2})\s+\$?(\d+\.\d{2})$'
        match = re.match(item_pattern, line)
        
        if match:
            description = match.group(1).strip()
            quantity = int(match.group(2))
            unit_price = float(match.group(3))
            total = float(match.group(4))
            
            # Validation
            expected_total = quantity * unit_price
            if abs(expected_total - total) < 0.01:
                item = {
                    "description": description,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total": total
                }
                items.append(item)
                print(f"   ✅ {description[:40]:<40} Qty:{quantity} ${total:.2f}")
            else:
                print(f"   ⚠️ Math error: {line}")
                print(f"      Expected: {quantity} × ${unit_price} = ${expected_total}, Got: ${total}")
        else:
            print(f"   ⚠️ No match: {line[:60]}")
    
    print(f"\n   📊 Total items extracted: {len(items)}")
    return items


def validate_extraction(data):
    """
    Validate the extracted data.
    """
    warnings = []
    
    print("\n🔎 VALIDATION CHECKS:")
    print("-" * 60)
    
    # Check 1: Line items sum
    if data['items'] and data['total_amount']:
        items_sum = sum(item['total'] for item in data['items'])
        difference = abs(items_sum - data['total_amount'])
        
        if difference > 0.01:
            warning = f"⚠️ Line items sum (${items_sum:.2f}) doesn't match total (${data['total_amount']:.2f})"
            warnings.append(warning)
            print(warning)
            print(f"   Missing: ${difference:.2f}")
        else:
            print(f"✅ Line items sum matches total: ${items_sum:.2f}")
    
    # Check 2: Email validation
    if data['bill_to']['email']:
        if '@' in data['bill_to']['email'] and '.' in data['bill_to']['email']:
            print(f"✅ Email format looks valid: {data['bill_to']['email']}")
        else:
            warning = f"⚠️ Email might be invalid: {data['bill_to']['email']}"
            warnings.append(warning)
            print(warning)
    
    # Check 3: Date validation
    if data['date']:
        year_match = re.search(r'(\d{4})', data['date'])
        if year_match:
            year = int(year_match.group(1))
            if 2020 <= year <= 2100:
                print(f"✅ Date year looks reasonable: {year}")
            else:
                warning = f"⚠️ Unusual year in date: {year}"
                warnings.append(warning)
                print(warning)
    
    print("-" * 60)
    
    return warnings


def calculate_confidence_score(data):
    """
    Calculate extraction confidence.
    """
    fields_to_check = [
        ('receipt_number', 20),
        ('date', 20),
        ('bill_to.name', 15),
        ('bill_to.email', 15),
        ('total_amount', 20),
        ('payment_method', 10)
    ]
    
    score = 0
    
    for field_path, weight in fields_to_check:
        value = data
        for key in field_path.split('.'):
            value = value.get(key) if isinstance(value, dict) else None
        
        if value:
            score += weight
    
    if data['items']:
        score += min(len(data['items']) * 2.5, 10)
    
    return min(score, 100)


if __name__ == "__main__":
    text_file = "data/processed/extracted_text.txt"
    
    print("="*70)
    print("🚀 STRUCTURED DATA EXTRACTION V3 (OCR ERROR CORRECTION)")
    print("="*70 + "\n")
    
    # Read text
    with open(text_file, 'r', encoding='utf-8') as f:
        ocr_text = f.read()
    
    # Extract fields
    extracted_data = extract_receipt_fields_v3(ocr_text)
    
    # Validate
    warnings = validate_extraction(extracted_data)
    
    # Calculate confidence
    confidence = calculate_confidence_score(extracted_data)
    extracted_data['extraction_confidence'] = confidence
    extracted_data['validation_warnings'] = warnings
    
    print("\n" + "="*70)
    print(f"📊 Extraction Confidence: {confidence:.0f}%")
    if warnings:
        print(f"⚠️ Validation Warnings: {len(warnings)}")
    else:
        print(f"✅ All validation checks passed!")
    print("="*70)
    
    # Display as JSON
    print("\n📄 STRUCTURED OUTPUT (JSON):")
    print("="*70)
    print(json.dumps(extracted_data, indent=2))
    print("="*70)
    
    # Save
    output_file = "data/processed/invoice_1_structured_v3.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved to: {output_file}")
    
    print("\n✅ Extraction complete!")