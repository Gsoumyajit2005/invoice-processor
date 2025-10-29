import streamlit as st
import os
import json
from datetime import datetime
from PIL import Image
import cv2
import numpy as np
import pytesseract
from src.detect_format import detect_invoice_format, get_format_recommendations

# Import our extraction logic
import sys
sys.path.append('src')
from extract_fields_v3 import (
    extract_receipt_fields_v3,
    validate_extraction,
    calculate_confidence_score
)

# Page configuration
st.set_page_config(
    page_title="Invoice Processor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">📄 Smart Invoice Processor</h1>', unsafe_allow_html=True)
st.markdown("### Extract structured data from invoices using OCR + Pattern Recognition")

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.info("""
    This app automatically extracts:
    - Receipt/Invoice number
    - Date
    - Customer information
    - Line items
    - Total amount
    - Payment method
    
    **Technology Stack:**
    - Tesseract OCR
    - OpenCV (image processing)
    - Pattern matching (regex)
    - OCR error correction
    """)
    
    st.header("📊 Stats")
    if 'processed_count' not in st.session_state:
        st.session_state.processed_count = 0
    st.metric("Invoices Processed", st.session_state.processed_count)

# Main content
tab1, tab2, tab3 = st.tabs(["📤 Upload & Process", "📚 Sample Invoices", "ℹ️ How It Works"])

with tab1:
    st.header("Upload Invoice")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an invoice image (JPG, PNG)", 
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear image of an invoice or receipt"
    )
    
    if uploaded_file is not None:
        # Create two columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📸 Original Image")
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)
            
            # Image info
            st.caption(f"Size: {image.size[0]} x {image.size[1]} pixels")
        
        with col2:
            st.subheader("🔄 Processing Status")
            
            # Processing button
            if st.button("🚀 Extract Data", type="primary"):
                with st.spinner("Processing invoice..."):
                    try:
                        # Convert PIL to OpenCV format
                        img_array = np.array(image)
                        
                        # Handle RGBA images
                        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
                            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
                        
                        # Step 1: OCR
                        st.write("🔍 Running OCR...")
                        ocr_text = pytesseract.image_to_string(img_array)

                        # Detect invoice format
                        st.write("🔍 Detecting invoice format...")
                        format_info = detect_invoice_format(ocr_text)
                        st.session_state.format_info = format_info
                        
                        # Step 2: Extract
                        st.write("🔧 Extracting structured data...")
                        extracted_data = extract_receipt_fields_v3(ocr_text)
                        
                        # Step 3: Validate
                        st.write("✅ Validating...")
                        warnings = validate_extraction(extracted_data)
                        
                        # Step 4: Calculate confidence
                        confidence = calculate_confidence_score(extracted_data)
                        extracted_data['extraction_confidence'] = confidence
                        extracted_data['validation_warnings'] = warnings
                        
                        # Store in session state
                        st.session_state.extracted_data = extracted_data
                        st.session_state.ocr_text = ocr_text
                        st.session_state.processed_count += 1
                        
                        st.success("✅ Processing complete!")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        # Display results if available
        if 'extracted_data' in st.session_state:
            st.markdown("---")
            st.header("📊 Extraction Results")

            # Format detection results
        if 'format_info' in st.session_state:
            format_info = st.session_state.format_info
            
            st.subheader("📋 Detected Format")
            
            col1, col2 = st.columns([2, 3])
            
            with col1:
                st.metric("Format Type", format_info['name'])
                st.metric("Detection Confidence", f"{format_info['confidence']:.0f}%")
                
                if format_info['supported']:
                    st.success("✅ Fully Supported")
                else:
                    st.warning("⚠️ Limited/No Support")
            
            with col2:
                st.write("**Detected Indicators:**")
                if format_info['indicators']:
                    for indicator in format_info['indicators']:
                        st.write(f"• {indicator}")
                else:
                    st.write("• No clear format indicators found")
                
                st.write("**Recommendations:**")
                for rec in get_format_recommendations(format_info):
                    st.write(rec)
            
            st.markdown("---")
            
            data = st.session_state.extracted_data
            
            # Confidence indicator
            confidence = data.get('extraction_confidence', 0)
            
            if confidence >= 80:
                st.markdown(f'<div class="success-box">✅ <strong>High Confidence: {confidence}%</strong> - Data extraction looks good!</div>', unsafe_allow_html=True)
            elif confidence >= 50:
                st.markdown(f'<div class="warning-box">⚠️ <strong>Medium Confidence: {confidence}%</strong> - Some fields may be missing or incorrect.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-box">❌ <strong>Low Confidence: {confidence}%</strong> - This invoice format may not be supported yet.</div>', unsafe_allow_html=True)
            
            # Display warnings
            if data.get('validation_warnings'):
                st.warning("⚠️ **Validation Warnings:**")
                for warning in data['validation_warnings']:
                    st.write(f"- {warning}")
            
            # Create result columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Receipt Number", data.get('receipt_number') or "Not found")
                st.metric("Date", data.get('date') or "Not found")
            
            with col2:
                st.metric("Total Amount", f"${data.get('total_amount'):.2f}" if data.get('total_amount') else "Not found")
                st.metric("Payment Method", data.get('payment_method') or "Not found")
            
            with col3:
                st.metric("Customer Name", data.get('bill_to', {}).get('name') or "Not found")
                st.metric("Customer Email", data.get('bill_to', {}).get('email') or "Not found")
            
            # Line items table
            if data.get('items'):
                st.subheader("🛒 Line Items")
                
                import pandas as pd
                df = pd.DataFrame(data['items'])
                
                # Format currency columns
                df['unit_price'] = df['unit_price'].apply(lambda x: f"${x:.2f}")
                df['total'] = df['total'].apply(lambda x: f"${x:.2f}")
                
                st.dataframe(df, use_container_width=True)
            else:
                st.info("ℹ️ No line items extracted")
            
            # JSON output
            with st.expander("📄 View Full JSON Output"):
                st.json(data)
            
            # Download button
            json_str = json.dumps(data, indent=2)
            st.download_button(
                label="💾 Download JSON",
                data=json_str,
                file_name=f"invoice_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            # Raw OCR text
            with st.expander("📝 View Raw OCR Text"):
                st.text(st.session_state.ocr_text)

with tab2:
    st.header("📚 Sample Invoices")
    st.write("Try these sample invoices to see how the system performs on different formats:")
    
    # Check for sample files
    sample_dir = "data/raw"
    if os.path.exists(sample_dir):
        sample_files = [f for f in os.listdir(sample_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
        
        if sample_files:
            cols = st.columns(3)
            for idx, filename in enumerate(sample_files[:6]):  # Show max 6
                with cols[idx % 3]:
                    img_path = os.path.join(sample_dir, filename)
                    img = Image.open(img_path)
                    st.image(img, caption=filename, use_container_width=True)
        else:
            st.info("No sample invoices found in data/raw/")
    else:
        st.info("Sample directory not found")

with tab3:
    st.header("ℹ️ How It Works")
    
    st.markdown("""
    ### Processing Pipeline
    
    ```
    1. 📸 Image Upload
       ↓
    2. 🔍 OCR (Tesseract)
       Extract raw text from image
       ↓
    3. 🔧 Error Correction
       Fix common OCR mistakes (e.g., 'J' → '1')
       ↓
    4. 🎯 Pattern Extraction
       Use regex to find specific fields
       ↓
    5. ✅ Validation
       Check if extracted data makes sense
       ↓
    6. 📊 Output JSON
       Structured, machine-readable data
    ```
    
    ### Supported Fields
    
    - ✅ Receipt/Invoice Number
    - ✅ Date
    - ✅ Customer Name & Email
    - ✅ Line Items (description, quantity, price)
    - ✅ Total Amount
    - ✅ Payment Method
    
    ### Known Limitations
    
    - ⚠️ Works best with **Template A** style invoices (retail receipts)
    - ⚠️ **Template B** style invoices (professional/business) may have lower accuracy
    - ⚠️ Image quality affects OCR accuracy
    - ⚠️ Pattern-based extraction requires consistent formatting
    
    ### Future Improvements
    
    - 🔮 Add ML-based extraction (LayoutLM) for multi-format support
    - 🔮 Improve OCR with image preprocessing
    - 🔮 Support for handwritten invoices
    - 🔮 Multi-language support
    """)
    
    st.info("💡 **Why not 100% accuracy?** Different companies use different invoice templates. This system is optimized for one format but gracefully handles others. A production system would use ML models (like LayoutLM) to learn from multiple formats.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    Built with Streamlit | Powered by Tesseract OCR | 
    <a href='https://github.com' target='_blank'>View on GitHub</a>
</div>
""", unsafe_allow_html=True)