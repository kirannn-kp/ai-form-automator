# AI Form Automator - Price Validation System

A sophisticated price consistency validation system that uses Azure AI services to detect discrepancies between numerical and written price representations in documents.

## Problem Solved

**Challenge**: Prices are stored numerically and textually across different documents. Manual checks are required to ensure both representations are consistent.

**Solution**: Automated price validation using Azure Document Intelligence and GPT-4.1 to detect inconsistencies in real-time.

## Features

- **Automated Text Extraction**: Uses Azure Document Intelligence to extract text from PDF documents
- **Price Validation**: GPT-4.1 powered analysis to find numerical vs written price mismatches
- **Currency Consistency**: Validates currency usage across documents  
- **Mathematical Validation**: Checks calculation accuracy
- **Structured Reports**: Generates detailed JSON reports with confidence scores
- **Azure AD Authentication**: Secure, enterprise-ready authentication

## Architecture

- **Azure Blob Storage**: Document storage and retrieval
- **Azure Document Intelligence**: PDF text extraction
- **Azure OpenAI (GPT-4.1)**: Price validation analysis
- **Python**: Processing orchestration

## Quick Start

### Prerequisites
- Azure CLI installed and authenticated (`az login`)
- Python 3.9+
- Access to Azure resources (provided in configuration)

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
Update `.env` file with your Azure endpoints (template provided in `.env.template`).

### Run Price Validation
```bash
python process_pdfs.py
```

## Output

The system generates:
- Individual validation reports for each document (`validation_reports/*.json`)
- Overall processing summary (`validation_reports/PROCESSING_SUMMARY.json`)
- Console output with real-time processing status

## Sample Results

```json
{
  "found_prices": [
    {
      "type": "numerical",
      "value": 50900,
      "currency": "EUR",
      "original_text": "EUR 50,900"
    },
    {
      "type": "written", 
      "value": 50800,
      "currency": "EUR",
      "original_text": "Fifty thousand eight hundred euros"
    }
  ],
  "inconsistencies": [
    "Written amount does not match numerical amount: EUR 100 discrepancy"
  ],
  "confidence_score": 0.98
}
```

## Enterprise Ready

- Secure Azure AD authentication (no API keys in code)
- Scalable architecture for high-volume processing
- Detailed logging and error handling
- Structured output for integration with business systems