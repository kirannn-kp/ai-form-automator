import os
import json
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional, env vars can be set in system
    pass

# Azure SDK imports
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from openai import AzureOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PriceValidationResult:
    """Data class for price validation results"""
    found_prices: List[Dict[str, Any]]
    inconsistencies: List[str]
    confidence_score: float
    validation_details: str

@dataclass
class DocumentProcessingResult:
    """Data class for complete document processing results"""
    document_name: str
    text_content: str
    price_validation: PriceValidationResult
    processing_status: bool
    error_message: Optional[str] = None

def validate_prices_with_gpt41(text_content: str, openai_client: AzureOpenAI) -> PriceValidationResult:
    """
    Validate price consistency using GPT-4.1 directly (no agents required)
    """
    try:
        validation_prompt = f"""
        You are a specialized price validation expert. Analyze the following document for price consistency issues.

        Tasks:
        1. Extract all numerical prices (e.g., $100.50, €25.99, 1,234.56 USD)
        2. Extract all written-out prices (e.g., "one hundred dollars", "twenty-five euros")
        3. Identify any discrepancies between numerical and textual price representations
        4. Check for currency inconsistencies
        5. Validate mathematical calculations involving prices

        Return your analysis in valid JSON format:
        {{
            "found_prices": [
                {{
                    "type": "numerical",
                    "value": 100.50,
                    "currency": "USD",
                    "location": "paragraph 1",
                    "original_text": "$100.50"
                }},
                {{
                    "type": "written",
                    "value": 100.50,
                    "currency": "USD", 
                    "location": "paragraph 1",
                    "original_text": "one hundred dollars and fifty cents"
                }}
            ],
            "inconsistencies": [
                "Price mismatch: $100.50 vs 'ninety dollars' in section 2"
            ],
            "confidence_score": 0.95,
            "validation_summary": "Found 2 price references, 1 inconsistency detected"
        }}

        Document content to analyze:
        {text_content[:3000]}...
        """

        response = openai_client.chat.completions.create(
            model="gpt-4.1",  # Your deployment name
            messages=[
                {
                    "role": "system", 
                    "content": "You are a precise financial document analyst. Always respond with valid JSON only."
                },
                {
                    "role": "user", 
                    "content": validation_prompt
                }
            ],
            temperature=0.1,
            max_tokens=2000
        )

        response_content = response.choices[0].message.content
        logger.info(f"GPT-4.1 response received: {len(response_content)} characters")

        try:
            # Parse JSON response
            result_data = json.loads(response_content)
            
            return PriceValidationResult(
                found_prices=result_data.get("found_prices", []),
                inconsistencies=result_data.get("inconsistencies", []),
                confidence_score=result_data.get("confidence_score", 0.0),
                validation_details=result_data.get("validation_summary", "Analysis completed")
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Return a structured response even if JSON parsing fails
            return PriceValidationResult(
                found_prices=[],
                inconsistencies=[],
                confidence_score=0.7,
                validation_details=f"Raw GPT response: {response_content[:200]}..."
            )
        
    except Exception as e:
        logger.error(f"GPT-4.1 validation error: {str(e)}")
        return PriceValidationResult(
            found_prices=[],
            inconsistencies=[f"GPT validation failed: {str(e)}"],
            confidence_score=0.0,
            validation_details=f"Error occurred: {str(e)}"
        )

def get_blob_files(blob_service_client: BlobServiceClient, container_name: str) -> List[str]:
    """Get list of PDF files from blob storage"""
    try:
        container_client = blob_service_client.get_container_client(container_name)
        pdf_files = [blob.name for blob in container_client.list_blobs() if blob.name.endswith('.pdf')]
        logger.info(f"Found {len(pdf_files)} PDF files in container '{container_name}'")
        return pdf_files
    except Exception as e:
        logger.error(f"Failed to list blob files: {str(e)}")
        return []

def extract_text_from_pdf(doc_intel_client: DocumentIntelligenceClient, blob_service_client: BlobServiceClient, 
                         container_name: str, pdf_file: str) -> str:
    """Extract text from PDF using Document Intelligence"""
    try:
        # Get blob content
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=pdf_file)
        blob_data = blob_client.download_blob().readall()
        
        # Analyze with Document Intelligence
        poller = doc_intel_client.begin_analyze_document(
            model_id="prebuilt-read",
            body=blob_data,
            content_type="application/pdf"
        )
        
        result = poller.result()
        text_content = result.content if result.content else ""
        
        logger.info(f"Extracted {len(text_content)} characters from {pdf_file}")
        return text_content
        
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_file}: {str(e)}")
        return ""

def save_processing_results(results: List[DocumentProcessingResult], output_folder: str):
    """Save processing results to JSON files"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Save individual results
    for result in results:
        if result.processing_status:
            filename = f"{result.document_name}_price_validation.json"
            filepath = os.path.join(output_folder, filename)
            
            # Convert to serializable format
            result_dict = {
                "document_name": result.document_name,
                "processing_status": result.processing_status,
                "price_validation": {
                    "found_prices": result.price_validation.found_prices,
                    "inconsistencies": result.price_validation.inconsistencies,
                    "confidence_score": result.price_validation.confidence_score,
                    "validation_details": result.price_validation.validation_details
                },
                "text_length": len(result.text_content),
                "error_message": result.error_message
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved results: {filepath}")

def create_summary_report(results: List[DocumentProcessingResult], output_folder: str):
    """Create overall summary report"""
    if not results:
        return
    
    successful_results = [r for r in results if r.processing_status]
    failed_results = [r for r in results if not r.processing_status]
    
    total_prices = sum(len(r.price_validation.found_prices) for r in successful_results)
    total_inconsistencies = sum(len(r.price_validation.inconsistencies) for r in successful_results)
    
    summary = {
        "processing_summary": {
            "total_documents": len(results),
            "successful_documents": len(successful_results),
            "failed_documents": len(failed_results),
            "total_prices_found": total_prices,
            "total_inconsistencies": total_inconsistencies,
            "average_confidence": sum(r.price_validation.confidence_score for r in successful_results) / len(successful_results) if successful_results else 0
        },
        "document_details": [
            {
                "document": r.document_name,
                "status": "✅ SUCCESS" if r.processing_status else "❌ FAILED",
                "prices_found": len(r.price_validation.found_prices) if r.processing_status else 0,
                "inconsistencies": len(r.price_validation.inconsistencies) if r.processing_status else 0,
                "confidence": r.price_validation.confidence_score if r.processing_status else 0,
                "error": r.error_message if r.error_message else None
            } for r in results
        ]
    }
    
    summary_path = os.path.join(output_folder, "PROCESSING_SUMMARY.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Print to console
    print("\\n" + "="*60)
    print("📊 PRICE VALIDATION SUMMARY")
    print("="*60)
    print(f"Documents Processed: {summary['processing_summary']['total_documents']}")
    print(f"Successful: {summary['processing_summary']['successful_documents']}")
    print(f"Failed: {summary['processing_summary']['failed_documents']}")
    print(f"Total Prices Found: {summary['processing_summary']['total_prices_found']}")
    print(f"Inconsistencies Found: {summary['processing_summary']['total_inconsistencies']}")
    print(f"Average Confidence: {summary['processing_summary']['average_confidence']:.2f}")
    print("="*60)
    
    # Show detailed inconsistencies for non-technical audience
    if successful_results and any(len(r.price_validation.inconsistencies) > 0 for r in successful_results):
        print("\\n🚨 PRICING ISSUES FOUND:")
        print("-" * 60)
        
        for result in successful_results:
            if result.price_validation.inconsistencies:
                print(f"\\n📄 Document: {result.document_name}")
                for i, inconsistency in enumerate(result.price_validation.inconsistencies, 1):
                    print(f"   ⚠️  Issue {i}: {inconsistency}")
                print(f"   💡 Confidence: {result.price_validation.confidence_score:.0%}")
                
        print("\\n" + "-" * 60)
        print("💰 BUSINESS IMPACT:")
        print("• These inconsistencies could lead to payment disputes")
        print("• Manual contract review recommended for flagged documents") 
        print("• Early detection prevents costly legal issues")
        print("-" * 60)
    else:
        print("\\n✅ NO PRICING ISSUES FOUND")
        print("All documents have consistent pricing information!")
        
    print("\\n📁 Detailed reports saved in: validation_reports/")
    print("="*60)
    
    logger.info(f"Summary report saved: {summary_path}")

def main():
    # Configuration from environment variables
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    document_intelligence_endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
    blob_account_url = os.getenv("BLOB_STORAGE_ACCOUNT_URL")
    blob_container_name = os.getenv("BLOB_CONTAINER_NAME", "price-validation-docs")
    
    # Validate required environment variables
    required_vars = {
        "AZURE_OPENAI_ENDPOINT": azure_openai_endpoint,
        "DOCUMENT_INTELLIGENCE_ENDPOINT": document_intelligence_endpoint,
        "BLOB_STORAGE_ACCOUNT_URL": blob_account_url
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables before running the script.")
        return
    
    try:
        # Initialize Azure clients
        credential = DefaultAzureCredential()
        
        # Azure OpenAI client for GPT-4.1 using Azure AD authentication
        # Get token for Cognitive Services scope
        def get_azure_openai_token():
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            return token.token
        
        openai_client = AzureOpenAI(
            azure_endpoint=azure_openai_endpoint,
            azure_ad_token_provider=get_azure_openai_token,  # Use token provider
            api_version="2025-01-01-preview"
        )
        
        # Blob Storage client
        blob_service_client = BlobServiceClient(
            account_url=blob_account_url,
            credential=credential
        )
        
        # Document Intelligence client
        doc_intel_client = DocumentIntelligenceClient(
            endpoint=document_intelligence_endpoint,
            credential=credential
        )
        
        logger.info("✅ All Azure clients initialized successfully")
        
        # Get list of PDF files from blob storage
        pdf_files = get_blob_files(blob_service_client, blob_container_name)
        
        if not pdf_files:
            logger.warning("No PDF files found in blob storage")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each PDF
        results = []
        for pdf_file in pdf_files:
            try:
                logger.info(f"Processing: {pdf_file}")
                
                # Extract text using Document Intelligence
                text_content = extract_text_from_pdf(
                    doc_intel_client, 
                    blob_service_client, 
                    blob_container_name, 
                    pdf_file
                )
                
                if text_content:
                    # Validate prices using GPT-4.1
                    validation_result = validate_prices_with_gpt41(
                        text_content, 
                        openai_client
                    )
                    
                    # Create processing result
                    doc_result = DocumentProcessingResult(
                        document_name=os.path.splitext(pdf_file)[0],
                        text_content=text_content,
                        price_validation=validation_result,
                        processing_status=True
                    )
                    
                    logger.info(f"✅ Successfully processed {pdf_file}")
                    logger.info(f"   Found {len(validation_result.found_prices)} prices")
                    logger.info(f"   Found {len(validation_result.inconsistencies)} inconsistencies")
                    logger.info(f"   Confidence: {validation_result.confidence_score:.2f}")
                
                else:
                    # Failed to extract text
                    doc_result = DocumentProcessingResult(
                        document_name=os.path.splitext(pdf_file)[0],
                        text_content="",
                        price_validation=PriceValidationResult([], ["Failed to extract text"], 0.0, "Text extraction failed"),
                        processing_status=False,
                        error_message="Failed to extract text from PDF"
                    )
                    
                    logger.error(f"❌ Failed to extract text from {pdf_file}")
                
                results.append(doc_result)
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {str(e)}")
                
                # Create failed result
                doc_result = DocumentProcessingResult(
                    document_name=os.path.splitext(pdf_file)[0],
                    text_content="",
                    price_validation=PriceValidationResult([], [f"Processing failed: {str(e)}"], 0.0, f"Error: {str(e)}"),
                    processing_status=False,
                    error_message=str(e)
                )
                results.append(doc_result)
        
        # Save results and create summary
        save_processing_results(results, "validation_reports")
        create_summary_report(results, "validation_reports")
        
        logger.info("✅ Price validation processing completed!")
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()