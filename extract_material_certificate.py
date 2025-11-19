"""
Material Certificate Extraction
Uses Azure Content Understanding to extract information from material certificates
"""

import os
import json
import requests
import time
from pathlib import Path

class ContentUnderstandingClient:
    """Client for Azure Content Understanding API"""
    
    def __init__(self, endpoint, api_key, api_version="2025-05-01-preview"):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.api_version = api_version
        self.headers = {
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "application/octet-stream"
        }
    
    def analyze_document(self, file_path):
        """Send document to Content Understanding for analysis"""
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        analyze_url = f"{self.endpoint}/contentunderstanding/analyzers/prebuilt-layout:analyze?api-version={self.api_version}&stringIndexType=textElements&features=keyValuePairs"
        
        print(f"[INFO] Sending document to Content Understanding...")
        response = requests.post(analyze_url, headers=self.headers, data=file_data)
        response.raise_for_status()
        
        operation_location = response.headers.get("operation-location")
        if not operation_location:
            raise Exception("No operation location returned")
        
        print("[INFO] Processing document...")
        return self._poll_results(operation_location)
    
    def _poll_results(self, operation_url, timeout=120, interval=2):
        """Poll the operation URL until completion"""
        start_time = time.time()
        poll_headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        
        while time.time() - start_time < timeout:
            response = requests.get(operation_url, headers=poll_headers)
            response.raise_for_status()
            result = response.json()
            
            status = result.get("status", "").lower()
            
            if status == "succeeded":
                print("[SUCCESS] Document processed successfully")
                return result
            elif status == "failed":
                raise Exception(f"Processing failed: {result}")
            
            time.sleep(interval)
        
        raise TimeoutError("Operation timed out")


def extract_material_info(result):
    """Extract material certificate information in simple format"""
    extracted_data = {
        "full_text": "",
        "tables": []
    }
    
    main_result = result.get("result", {})
    contents = main_result.get("contents", [])
    
    if not contents:
        print("[WARNING] No contents found in result")
        return extracted_data
    
    for content in contents:
        # Extract text content
        markdown = content.get("markdown", "")
        if markdown:
            extracted_data["full_text"] = markdown
            print(f"[INFO] Extracted text: {len(markdown)} characters")
        
        # Extract tables
        tables = content.get("tables", [])
        if tables:
            print(f"[INFO] Found {len(tables)} tables")
            
            for table_idx, table in enumerate(tables):
                row_count = table.get("rowCount", 0)
                col_count = table.get("columnCount", 0)
                
                # Create table structure
                table_rows = []
                for _ in range(row_count):
                    table_rows.append([""] * col_count)
                
                # Fill in cells
                for cell in table.get("cells", []):
                    row = cell.get("rowIndex", 0)
                    col = cell.get("columnIndex", 0)
                    content_text = cell.get("content", "").strip()
                    
                    if row < row_count and col < col_count:
                        table_rows[row][col] = content_text
                
                # Save non-empty tables
                if any(any(cell for cell in row) for row in table_rows):
                    extracted_data["tables"].append({
                        "table_number": table_idx + 1,
                        "rows": table_rows
                    })
    
    return extracted_data


def save_results(data, output_path):
    """Save extracted data to JSON file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[SAVED] Results saved to: {output_path}")


def print_summary(data):
    """Print a summary of extracted information"""
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)
    
    # Text content
    full_text = data.get("full_text", "")
    if full_text:
        print(f"\nExtracted {len(full_text)} characters of text")
        lines = [line for line in full_text.split('\n')[:3] if line.strip()]
        if lines:
            print("\nPreview:")
            for line in lines:
                preview = line[:70] + "..." if len(line) > 70 else line
                print(f"  {preview}")
    
    # Tables
    tables = data.get("tables", [])
    if tables:
        print(f"\nExtracted {len(tables)} tables")
        for table in tables:
            rows = table.get("rows", [])
            if rows:
                cols = len(rows[0]) if rows else 0
                print(f"  - Table {table['table_number']}: {len(rows)} rows x {cols} columns")
    
    print("\n" + "="*60)


def main():
    """Main execution"""
    
    # Configuration
    ENDPOINT = "Endpoint_URL_here"
    API_KEY = "API_Key_here"
    
    # Paths
    PDF_FOLDER = "examplePdf"
    OUTPUT_FOLDER = "material_certificates_output"
    
    # Initialize client
    client = ContentUnderstandingClient(ENDPOINT, API_KEY)
    
    # Process all PDFs
    pdf_files = list(Path(PDF_FOLDER).glob("*.[pP][dD][fF]"))
    
    if not pdf_files:
        print(f"[ERROR] No PDF files found in {PDF_FOLDER}")
        return
    
    print(f"\n[INFO] Found {len(pdf_files)} PDF file(s) to process\n")
    
    for pdf_path in pdf_files:
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_path.name}")
        print(f"{'='*60}")
        
        try:
            # Analyze document
            result = client.analyze_document(str(pdf_path))
            
            # Extract information
            extracted_data = extract_material_info(result)
            
            # Save results
            output_filename = f"{pdf_path.stem}_extracted.json"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            save_results(extracted_data, output_path)
            
            # Print summary
            print_summary(extracted_data)
            
        except Exception as e:
            print(f"[ERROR] Failed to process {pdf_path.name}: {e}")


if __name__ == "__main__":
    main()
