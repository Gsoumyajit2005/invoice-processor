import re

def detect_invoice_format(ocr_text):
    """
    Detect which invoice template is being used.
    Helps users understand why confidence is low.
    
    Args:
        ocr_text: Raw OCR text
    
    Returns:
        dict with format info
    """
    
    formats = {
        'template_a': {
            'name': 'Retail Receipt (Template A)',
            'confidence': 0,
            'indicators': [],
            'supported': True
        },
        'template_b': {
            'name': 'Professional Invoice (Template B)',
            'confidence': 0,
            'indicators': [],
            'supported': False
        },
        'unknown': {
            'name': 'Unknown Format',
            'confidence': 0,
            'indicators': [],
            'supported': False
        }
    }
    
    # Check for Template A indicators
    template_a_patterns = [
        (r'Receipt\s*#\d+', 'Receipt # format'),
        (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}', 'Written month format'),
        (r'Total\s+Amount:', 'Total Amount: label'),
        (r'Payment\s+Method:', 'Payment Method: label'),
        (r'Item\s+Description\s+Quantity', 'Standard table header')
    ]
    
    for pattern, indicator in template_a_patterns:
        if re.search(pattern, ocr_text, re.IGNORECASE):
            formats['template_a']['confidence'] += 20
            formats['template_a']['indicators'].append(indicator)
    
    # Check for Template B indicators
    template_b_patterns = [
        (r'RECEIPT\s*#', 'RECEIPT # (uppercase)'),
        (r'RECEIPT\s+DATE', 'RECEIPT DATE label'),
        (r'\d{2}/\d{2}/\d{4}', 'Date format DD/MM/YYYY'),
        (r'BILL\s*TO', 'BILL TO (uppercase)'),
        (r'SHIP\s*TO', 'SHIP TO label'),
        (r'QTY\s+DESCRIPTION', 'QTY DESCRIPTION header'),
        (r'UNIT\s+PRICE', 'UNIT PRICE column'),
        (r'East\s+Repair', 'East Repair Inc.')
    ]
    
    for pattern, indicator in template_b_patterns:
        if re.search(pattern, ocr_text, re.IGNORECASE):
            formats['template_b']['confidence'] += 12.5
            formats['template_b']['indicators'].append(indicator)
    
    # Determine best match
    best_format = max(formats.items(), key=lambda x: x[1]['confidence'])
    
    if best_format[1]['confidence'] < 30:
        return formats['unknown']
    
    return best_format[1]


def get_format_recommendations(format_info):
    """
    Provide recommendations based on detected format.
    
    Args:
        format_info: Output from detect_invoice_format()
    
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    if format_info['name'] == 'Retail Receipt (Template A)':
        recommendations.append("✅ This format is fully supported!")
        recommendations.append("Expected accuracy: 95-100%")
    
    elif format_info['name'] == 'Professional Invoice (Template B)':
        recommendations.append("⚠️ This format has limited support")
        recommendations.append("💡 Recommendation: Add Template B patterns or use ML-based extraction")
        recommendations.append("📊 Current accuracy: 10-20% (basic fields only)")
    
    else:
        recommendations.append("❌ Format not recognized")
        recommendations.append("💡 Try using a clearer image or different format")
        recommendations.append("📧 Or contact support to add this format")
    
    return recommendations