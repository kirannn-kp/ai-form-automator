# Azure Document Intelligence POC

Professional proof-of-concept for document extraction using Azure Document Intelligence.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure .env with Azure credentials
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your-endpoint
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key

# Run POC
python document_intelligence_demo.py
```

## Features

- Extracts text, tables, and structure from PDF documents
- Processes 2-page document in ~8 seconds
- Outputs structured JSON with all extracted data
- Professional, production-ready code

## Output

Results saved to `extraction_output/` containing:
- Complete document text
- Table data with rows/columns/cells
- Page-by-page line extraction
- Document metadata and statistics
