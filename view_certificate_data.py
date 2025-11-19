"""
View extracted material certificate data in a readable format
"""

import json
import sys
from pathlib import Path

def print_header(text, char="="):
    """Print a formatted header"""
    width = 80
    print(f"\n{char * width}")
    print(f"{text:^{width}}")
    print(f"{char * width}\n")

def view_extraction_results(json_file):
    """Display the extracted certificate data in a readable format"""
    
    # Load the JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print_header("MATERIAL CERTIFICATE EXTRACTION RESULTS", "=")
    
    # Extracted Content
    full_text = data.get("full_text", "")
    
    if full_text:
        print_header("Extracted Text Content", "-")
        print(full_text)
    
    # Tables
    tables = data.get("tables", [])
    
    if tables:
        print_header(f"Tables ({len(tables)} found)", "-")
        
        for table in tables:
            rows = table.get("rows", [])
            if rows:
                cols = len(rows[0]) if rows else 0
                print(f"\n{'─' * 80}")
                print(f"Table {table['table_number']}: {len(rows)} rows x {cols} columns")
                print(f"{'─' * 80}\n")
                
                # Display table
                for row_idx, row in enumerate(rows):
                    row_text = [cell if cell else "—" for cell in row]
                    print(f"Row {row_idx}: {' | '.join(row_text)}")
                print()

def main():
    """Main function"""
    
    # Get JSON file path
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # Default to the most recent file
        output_folder = Path("material_certificates_output")
        if not output_folder.exists():
            print("[ERROR] No output folder found. Run extract_material_certificate.py first.")
            return
        
        json_files = list(output_folder.glob("*.json"))
        if not json_files:
            print("[ERROR] No JSON files found in output folder.")
            return
        
        # Get the most recent file
        json_file = max(json_files, key=lambda p: p.stat().st_mtime)
        print(f"[INFO] Loading: {json_file.name}\n")
    
    # View the results
    view_extraction_results(json_file)
    
    print_header("Viewing Complete", "=")

if __name__ == "__main__":
    main()
