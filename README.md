# AI Form Automator

This project uses Azure Document Intelligence to extract structured data from PDF forms and then uses Azure OpenAI GPT-4 to convert that data into structured XML format.

## Features

✅ **Azure Document Intelligence Integration**: Extracts structured data from PDF forms  
✅ **OpenAI GPT-4 XML Generation**: Converts extracted data to structured XML format  
✅ **German Language Support**: Proper handling of German characters and medical terminology  
✅ **XML Schema Compliance**: Generates XML matching your required structure  
✅ **Batch Processing**: Processes multiple PDFs automatically  
✅ **Comprehensive Logging**: Detailed logging and error handling  

## Prerequisites

- Azure Document Intelligence resource
- Azure OpenAI resource with GPT-4 model deployed
- Python 3.8+

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Azure services in `.env` file:**
   ```bash
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your-endpoint
   AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key
   AZURE_OPENAI_ENDPOINT=your-endpoint
   AZURE_OPENAI_KEY=your-key
   AZURE_OPENAI_GPT4_DEPLOYMENT_NAME=gpt-4o
   ```

3. **Place PDF files in `examplePdf/` folder**

4. **Run the processor:**
   ```bash
   python simple_enhanced_processor.py
   ```

## Scripts

- **`simple_enhanced_processor.py`**: Main processing script - extracts data from PDFs and converts to XML
- **`process_pdfs.py`**: Alternative script that processes existing JSON files and converts them to XML (cleaned and optimized)

## Usage

### Full Processing (PDF → JSON → XML)
```bash
python simple_enhanced_processor.py
```

### JSON to XML Only
```bash
python process_pdfs.py
```

## Example Files

The project includes a complete working example:
- **Input**: `examplePdf/Tauchsport igel 2025 ASD-5491.pdf` 
- **Extracted Data**: `json_output/Tauchsport igel 2025 ASD-5491.json`
- **Generated XML**: `xml_output/Tauchsport igel 2025 ASD-5491.xml`

## Project Structure

```
ai-form-automator/
├── simple_enhanced_processor.py    # Main processing script
├── process_pdfs.py                 # Original implementation
├── .env                           # Azure credentials
├── requirements.txt               # Dependencies
├── README.md                      # This file
├── examplePdf/                    # Input PDF files
├── json_output/                   # Extracted JSON data
└── xml_output/                    # Generated XML files
```
