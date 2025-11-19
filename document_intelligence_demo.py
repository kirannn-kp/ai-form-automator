
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

# Load environment variables
load_dotenv()

# Configuration
PDF_FOLDER = "examplePdf"
OUTPUT_FOLDER = "extraction_output"
TARGET_PDF = "E0S4501264722.PDF"

def ensure_output_directory():
    """Create output directory if it doesn't exist"""
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_document(pdf_path, endpoint, api_key):
    print("\n" + "="*80)
    print("Azure Document Intelligence - Extraction Demo")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Document: {os.path.basename(pdf_path)}")
    print("="*80 + "\n")
    
    try:
        # Initialize Document Intelligence client
        client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        
        print(f"Processing document: {os.path.basename(pdf_path)}")
        print("Analyzing with Azure Document Intelligence Layout Model...")
        
        start_time = time.time()
        
        # Read PDF file
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()
        
        # Analyze document using prebuilt-layout model
        poller = client.begin_analyze_document(
            "prebuilt-layout",
            pdf_content,
            content_type="application/pdf"
        )
        
        # Wait for completion
        result = poller.result()
        processing_time = time.time() - start_time
        
        print(f"Extraction completed in {processing_time:.2f} seconds\n")
        
        # Calculate statistics
        stats = {
            "pages": len(result.pages) if result.pages else 0,
            "paragraphs": len(result.paragraphs) if result.paragraphs else 0,
            "tables": len(result.tables) if result.tables else 0,
            "key_value_pairs": len(result.key_value_pairs) if result.key_value_pairs else 0,
            "lines": sum(len(page.lines) for page in result.pages) if result.pages else 0,
            "words": sum(len(page.words) for page in result.pages) if result.pages else 0
        }
        
        print("Extraction Statistics:")
        print(f"  Pages: {stats['pages']}")
        print(f"  Paragraphs: {stats['paragraphs']}")
        print(f"  Tables: {stats['tables']}")
        print(f"  Key-Value Pairs: {stats['key_value_pairs']}")
        print(f"  Lines: {stats['lines']}")
        print(f"  Words: {stats['words']}")
        print()
        
        return result, stats, processing_time
        
    except Exception as e:
        print(f"Error during extraction: {str(e)}")
        raise

def save_results(pdf_filename, result, stats):

    base_name = os.path.splitext(pdf_filename)[0]
    json_path = os.path.join(OUTPUT_FOLDER, f"{base_name}_extraction.json")
    
    # Convert result to dictionary format
    json_data = {
        "document": pdf_filename,
        "extraction_timestamp": datetime.now().isoformat(),
        "statistics": stats,
        "content": result.content if result.content else "",
        "pages": [],
        "tables": [],
        "key_value_pairs": []
    }
    
    # Extract pages
    if result.pages:
        for page in result.pages:
            page_data = {
                "page_number": page.page_number,
                "width": page.width,
                "height": page.height,
                "unit": page.unit,
                "lines": [line.content for line in page.lines] if page.lines else []
            }
            json_data["pages"].append(page_data)
    
    # Extract tables
    if result.tables:
        for idx, table in enumerate(result.tables):
            table_data = {
                "table_index": idx,
                "row_count": table.row_count,
                "column_count": table.column_count,
                "cells": []
            }
            for cell in table.cells:
                table_data["cells"].append({
                    "row_index": cell.row_index,
                    "column_index": cell.column_index,
                    "content": cell.content,
                    "row_span": cell.row_span if hasattr(cell, 'row_span') else 1,
                    "column_span": cell.column_span if hasattr(cell, 'column_span') else 1
                })
            json_data["tables"].append(table_data)
    
    # Extract key-value pairs
    if result.key_value_pairs:
        for kv in result.key_value_pairs:
            json_data["key_value_pairs"].append({
                "key": kv.key.content if kv.key else "",
                "value": kv.value.content if kv.value else "",
                "confidence": kv.confidence if hasattr(kv, 'confidence') else 0.0
            })
    
    # Save to file
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {json_path}")
    return json_path

def print_summary(total_time, stats):
    """Print summary of extraction"""
    print("\n" + "="*80)
    print("Extraction Summary")
    print("="*80)
    print(f"Total Processing Time: {total_time:.2f} seconds")
    print(f"Pages Processed: {stats['pages']}")
    print(f"Tables Extracted: {stats['tables']}")
    print(f"Key-Value Pairs Found: {stats['key_value_pairs']}")
    print(f"Output Directory: {OUTPUT_FOLDER}/")
    print("="*80 + "\n")

def main():
    """Main execution"""
    demo_start_time = time.time()
    
    # Load configuration
    print("Loading configuration...")
    doc_intel_endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
    doc_intel_key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
    
    # Validate configuration
    if not doc_intel_endpoint or not doc_intel_key:
        print("Error: Missing Azure Document Intelligence configuration")
        print("Please check your .env file for:")
        print("  - AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        print("  - AZURE_DOCUMENT_INTELLIGENCE_KEY")
        return
    
    print("Configuration loaded successfully\n")
    
    # Ensure output directory exists
    ensure_output_directory()
    
    # Check if target PDF exists
    pdf_path = os.path.join(PDF_FOLDER, TARGET_PDF)
    if not os.path.exists(pdf_path):
        print(f"Error: Target PDF not found: {pdf_path}")
        return
    
    try:
        # Extract document
        result, stats, extraction_time = extract_document(
            pdf_path, doc_intel_endpoint, doc_intel_key
        )
        
        # Save results
        json_path = save_results(TARGET_PDF, result, stats)
        
        # Print summary
        total_time = time.time() - demo_start_time
        print_summary(total_time, stats)
        
        print("POC completed successfully!")
        
    except Exception as e:
        print(f"\nPOC failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
