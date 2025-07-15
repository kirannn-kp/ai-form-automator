"""
Clean PDF Processing Script

This script processes JSON files (extracted from PDFs) and converts them to XML format
using Azure OpenAI GPT-4.

Usage: python process_pdfs.py
"""

import os
import requests
import json
from dotenv import load_dotenv
from typing import Callable, Any, Optional
import time
from pathlib import Path
import xml.etree.ElementTree as ET

# Load environment variables
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv(dotenv_path=dotenv_path)

# Verify environment variables are loaded (without exposing values)
if os.getenv('GPT41_KEY'):
    print("✅ GPT41_KEY loaded successfully")
if os.getenv('GPT4O_KEY'):
    print("✅ GPT4O_KEY loaded successfully")

class AzureContentUnderstandingClient:
    """
    Azure Content Understanding Client for document analysis
    """
    def __init__(
        self,
        endpoint: str,
        api_version: str,
        subscription_key: Optional[str] = None,
        token_provider: Optional[Callable[[], str]] = None,
        x_ms_useragent: str = "cu-sample-code",
    ) -> None:
        if not subscription_key and token_provider is None:
            raise ValueError(
                "Either subscription key or token provider must be provided"
            )
        if not api_version:
            raise ValueError("API version must be provided")
        if not endpoint:
            raise ValueError("Endpoint must be provided")

        self._endpoint: str = endpoint.rstrip("/")
        self._api_version: str = api_version
        self._headers: dict[str, str] = self._get_headers(
            subscription_key, token_provider and token_provider(), x_ms_useragent
        )

    def begin_analyze(self, analyzer_id: str, file_location: str):
        """Begin document analysis"""
        if Path(file_location).exists():
            with open(file_location, "rb") as file:
                data = file.read()
            headers = {"Content-Type": "application/octet-stream"}
        elif "https://" in file_location or "http://" in file_location:
            data = {"url": file_location}
            headers = {"Content-Type": "application/json"}
        else:
            raise ValueError("File location must be a valid path or URL.")

        headers.update(self._headers)
        if isinstance(data, dict):
            response = requests.post(
                url=self._get_analyze_url(
                    self._endpoint, self._api_version, analyzer_id
                ),
                headers=headers,
                json=data,
            )
        else:
            response = requests.post(
                url=self._get_analyze_url(
                    self._endpoint, self._api_version, analyzer_id
                ),
                headers=headers,
                data=data,
            )

        response.raise_for_status()
        return response

    def poll_result(
        self,
        response: requests.Response,
        timeout_seconds: int = 120,
        polling_interval_seconds: int = 2,
    ) -> dict[str, Any]:
        """Poll for analysis results"""
        operation_location = response.headers.get("operation-location", "")
        if not operation_location:
            raise ValueError("Operation location not found in response headers.")

        start_time = time.time()
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                raise TimeoutError(
                    f"Operation timed out after {timeout_seconds:.2f} seconds."
                )

            response = requests.get(operation_location, headers=self._headers)
            response.raise_for_status()
            result = response.json()
            status = result.get("status", "").lower()
            if status == "succeeded":
                return result
            elif status == "failed":
                raise RuntimeError("Request failed.")
            time.sleep(polling_interval_seconds)

    def _get_analyze_url(self, endpoint: str, api_version: str, analyzer_id: str):
        """Get analysis URL"""
        return f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze?api-version={api_version}&stringEncoding=utf16"

    def _get_headers(
        self, subscription_key: Optional[str], api_token: Optional[str], x_ms_useragent: str
    ) -> dict[str, str]:
        """Get request headers"""
        headers = (
            {"Ocp-Apim-Subscription-Key": subscription_key}
            if subscription_key
            else {"Authorization": f"Bearer {api_token}"}
        )
        headers["x-ms-useragent"] = x_ms_useragent
        return headers

    def begin_analyze(self, analyzer_id: str, file_location: str):
        if Path(file_location).exists():
            with open(file_location, "rb") as file:
                data = file.read()
            headers = {"Content-Type": "application/octet-stream"}
        elif "https://" in file_location or "http://" in file_location:
            data = {"url": file_location}
            headers = {"Content-Type": "application/json"}
        else:
            raise ValueError("File location must be a valid path or URL.")

        headers.update(self._headers)
        if isinstance(data, dict):
            response = requests.post(
                url=self._get_analyze_url(
                    self._endpoint, self._api_version, analyzer_id
                ),
                headers=headers,
                json=data,
            )
        else:
            response = requests.post(
                url=self._get_analyze_url(
                    self._endpoint, self._api_version, analyzer_id
                ),
                headers=headers,
                data=data,
            )

        response.raise_for_status()
        return response

    def poll_result(
        self,
        response: requests.Response,
        timeout_seconds: int = 120,
        polling_interval_seconds: int = 2,
    ) -> dict[str, Any]:
        operation_location = response.headers.get("operation-location", "")
        if not operation_location:
            raise ValueError("Operation location not found in response headers.")

        start_time = time.time()
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                raise TimeoutError(
                    f"Operation timed out after {timeout_seconds:.2f} seconds."
                )

            response = requests.get(operation_location, headers=self._headers)
            response.raise_for_status()
            result = response.json()
            status = result.get("status", "").lower()
            if status == "succeeded":
                return result
            elif status == "failed":
                raise RuntimeError("Request failed.")
            time.sleep(polling_interval_seconds)

    def _get_analyze_url(self, endpoint: str, api_version: str, analyzer_id: str):
        return f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze?api-version={api_version}&stringEncoding=utf16"

    def _get_headers(
        self, subscription_key: Optional[str], api_token: Optional[str], x_ms_useragent: str
    ) -> dict[str, str]:
        headers = (
            {"Ocp-Apim-Subscription-Key": subscription_key}
            if subscription_key
            else {"Authorization": f"Bearer {api_token}"}
        )
        headers["x-ms-useragent"] = x_ms_useragent
        return headers

# Removed unused functions related to image-based processing and PDF-to-image conversion
# Removed functions:
# - convert_pdf_to_images
# - send_image_to_gpt41
# - send_image_to_gpt41_with_original_xml

def send_markdown_to_gpt4o(markdown_content, gpt4o_url, gpt4o_key):
    headers = {
        'api-key': gpt4o_key,
        'Content-Type': 'application/json'
    }
    data = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI that converts Markdown tables into structured XML matching a predefined schema. "
                    "The schema should match the structure and content of the original 'Honorarvereinbarung Eventrekorder' form, "
                    "including metadata, labels, and their associated values. Ensure the XML output replicates the original form's "
                    "layout and hierarchy accurately. Validate the XML to ensure it is well-formed and matches the original structure. "
                    "If a field is empty in the form, represent it as an empty tag in the XML."
                )
            },
            {
                "role": "user",
                "content": f"Please convert the following Markdown table into XML with the expected structure and content:\n{markdown_content}"
            }
        ]
    }

    try:
        response = requests.post(gpt4o_url, headers=headers, json=data)
        response.raise_for_status()
        print("Successfully converted Markdown to XML.")
        return response.json()  # Return the full JSON response
    except requests.exceptions.RequestException as e:
        print(f"Failed to convert Markdown to XML. Error: {e}")
        if response is not None:
            print("Response Content:", response.text)
        return None

def validate_and_save_xml(xml_content, output_path):
    try:
        # Print the XML content for debugging
        print("Generated XML Content:")
        print(xml_content)

        # Remove BOM if present
        if xml_content.startswith('\ufeff'):
            xml_content = xml_content[1:]

        # Validate XML structure
        ET.fromstring(xml_content)
        print("XML is well-formed.")

        # Ensure the output folder exists
        output_folder = os.path.dirname(output_path)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Save XML to file
        with open(output_path, 'w', encoding='utf-8') as xml_file:
            xml_file.write(xml_content)
            print(f"Saved XML: {output_path}")
    except ET.ParseError as e:
        print(f"XML validation failed: {e}")
        # Save the XML for debugging even if validation fails
        output_folder = os.path.dirname(output_path)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        with open(output_path, 'w', encoding='utf-8') as xml_file:
            xml_file.write(xml_content)
            print(f"Saved invalid XML for debugging: {output_path}")
        return False
    except Exception as e:
        print(f"Unexpected error during XML validation or saving: {e}")
        return False
    return True

def debug_extracted_data(markdown_content):
    print("Extracted Markdown Content:")
    print(markdown_content)

def send_pdf_to_content_understanding(pdf_path, content_understanding_url, api_key):
    """
    Sends a PDF to the Content Understanding service and retrieves structured data in JSON format.
    """
    headers = {
        'api-key': api_key,
        'Content-Type': 'application/pdf'
    }

    with open(pdf_path, 'rb') as pdf_file:
        response = requests.post(content_understanding_url, headers=headers, data=pdf_file)

    response.raise_for_status()
    print("Successfully processed PDF to JSON.")
    return response.json()

def convert_json_to_xml(json_data, gpt4o_url, gpt4o_key):
    """
    Sends JSON data to GPT-4o for conversion to XML format.
    """
    headers = {
        'api-key': gpt4o_key,
        'Content-Type': 'application/json'
    }

    data = {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Please convert the following JSON data into XML format. Ensure the XML structure matches the schema used in the provided examples."
                )
            },
            {
                "role": "user",
                "content": json.dumps(json_data)
            }
        ]
    }

    response = requests.post(gpt4o_url, headers=headers, json=data)
    response.raise_for_status()
    print("Successfully converted JSON to XML.")
    return response.json()["choices"][0]["message"]["content"]

def convert_json_to_xml_v2(json_data, gpt4o_url, gpt4o_key):
    """
    Converts JSON data to XML format using GPT-4o
      Args:
        json_data: The JSON data to convert
        gpt4o_url: Azure OpenAI GPT-4o endpoint URL
        gpt4o_key: Azure OpenAI API key
        
    Returns:
        XML content as string
    """
    headers = {
        'api-key': gpt4o_key,
        'Content-Type': 'application/json'
    }

    data = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert medical forms data converter. Your job is to convert structured JSON data (from a medical form) into a well-formed XML document that matches the original form's structure and content as closely as possible.\n"
                    "- The XML must have a <root> element, and all relevant metadata, fields, and content from the JSON must be mapped to appropriate XML elements and attributes.\n"
                    "- For each patient field (such as name, date of birth, address, etc.), create a <label> element with a 'title' attribute containing the value or a placeholder (e.g., §{pat_complete}§, §{pat_dob}§, etc.).\n"
                    "- Include all static text, instructions, and legal/consent language from the form as <label> elements, preserving their order and formatting.\n"
                    "- Use the correct form name, title, and section headers as found in the JSON or inferred from the content.\n"
                    "- If the JSON contains page, table, or key-value data, map these to XML in a way that preserves the original form's structure.\n"
                    "- Do NOT include any markdown, explanations, or comments—output ONLY the XML.\n"
                    "- The XML must be valid and ready for use in a medical forms system.\n"
                    "- If a field is missing, use a placeholder in the format §{field_name}§.\n"
                )
            },
            {
                "role": "user",
                "content": f"Convert this JSON data to the complete XML structure for a diving sports examination form:\n{json.dumps(json_data, indent=2)}"
            }
        ]
    }

    response = requests.post(gpt4o_url, headers=headers, json=data)
    response.raise_for_status()
    print("Successfully converted JSON to XML.")    # Extract XML content from response
    xml_content = response.json()["choices"][0]["message"]["content"]
    
    # Clean up the response - remove any markdown formatting or extra text
    if "````xml" in xml_content:
        xml_content = xml_content.split("````xml")[1].split("````")[0].strip()
    elif "```xml" in xml_content:
        xml_content = xml_content.split("```xml")[1].split("```")[0].strip()
    elif "```" in xml_content:
        xml_content = xml_content.split("```")[1].split("```")[0].strip()
    
    # Remove any remaining markdown backticks
    xml_content = xml_content.replace("````", "").replace("```", "")
    
    # Remove any leading/trailing text before <?xml or <root>
    if "<?xml" in xml_content:
        xml_content = xml_content[xml_content.find("<?xml"):]
    elif "<root>" in xml_content:
        xml_content = xml_content[xml_content.find("<root>"):]
    
    # Remove any text after </root>
    if "</root>" in xml_content:
        xml_content = xml_content[:xml_content.find("</root>") + 7]
    
    # Remove any explanatory text or comments that GPT might have added
    lines = xml_content.split('\n')
    clean_lines = []
    in_comment_block = False
    
    for line in lines:
        # Skip lines that look like explanations or markdown
        if line.strip().startswith('###') or line.strip().startswith('**') or line.strip().startswith('- '):
            continue
        if 'Explanation:' in line or 'explanation:' in line:
            in_comment_block = True
            continue
        if in_comment_block and not line.strip().startswith('<'):
            continue
        if line.strip().startswith('<') or line.strip() == '':
            in_comment_block = False
            clean_lines.append(line)
    
    xml_content = '\n'.join(clean_lines).strip()
    
    return xml_content

def send_pdf_to_content_understanding_v2(pdf_path, analyzer_id, client):
    """
    Sends a PDF to the Content Understanding service and retrieves structured data in JSON format.
    """
    response = client.begin_analyze(analyzer_id, pdf_path)
    result = client.poll_result(response)
    print("Successfully processed PDF to JSON.")
    return result

def process_pdf_workflow(pdf_folder, json_output_folder, xml_output_folder, content_understanding_url, gpt4o_url, api_keys):
    """
    Processes PDFs using the Content Understanding service and GPT-4o for JSON-to-XML conversion.
    """
    if not os.path.exists(json_output_folder):
        os.makedirs(json_output_folder)

    if not os.path.exists(xml_output_folder):
        os.makedirs(xml_output_folder)

    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.endswith('.pdf'):
            pdf_path = os.path.join(pdf_folder, pdf_file)

            # Step 1: Extract JSON from PDF
            json_data = send_pdf_to_content_understanding(
                pdf_path, content_understanding_url, api_keys['content_understanding']
            )

            # Save JSON output
            json_filename = f"{os.path.splitext(pdf_file)[0]}.json"
            json_path = os.path.join(json_output_folder, json_filename)
            with open(json_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
            print(f"Saved JSON: {json_path}")

            # Step 2: Convert JSON to XML
            xml_data = convert_json_to_xml(
                json_data, gpt4o_url, api_keys['gpt4o']
            )

            # Ensure XML data is encoded as UTF-8 before writing
            xml_data = xml_data.encode('utf-8').decode('utf-8')
            xml_path = os.path.join(xml_output_folder, f"{os.path.splitext(json_file)[0]}.xml")
            with open(xml_path, mode='w', encoding='utf-8') as xml_file:
                xml_file.write(xml_data)
            print(f"Saved XML: {xml_path}")

def process_pdf_workflow_v2(pdf_folder, json_output_folder, client):
    """
    Processes PDFs using the Content Understanding service and saves JSON outputs.
    """
    analyzer_id = "ambulappsanalyzer"  # Use the provided Analyzer ID

    if not os.path.exists(json_output_folder):
        os.makedirs(json_output_folder)

    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.endswith('.pdf'):
            pdf_path = os.path.join(pdf_folder, pdf_file)

            # Step 1: Extract JSON from PDF using Content Understanding
            json_data = send_pdf_to_content_understanding_v2(
                pdf_path, analyzer_id, client
            )

            # Save JSON output
            json_filename = f"{os.path.splitext(pdf_file)[0]}.json"
            json_path = os.path.join(json_output_folder, json_filename)
            with open(json_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
            print(f"Saved JSON: {json_path}")

def process_json_to_xml_workflow(json_folder, xml_output_folder, gpt4o_url, gpt4o_key):
    """
    Processes JSON files and converts them to XML using GPT-4o.
    """
    if not os.path.exists(xml_output_folder):
        os.makedirs(xml_output_folder)

    for json_file in os.listdir(json_folder):
        if json_file.endswith('.json'):
            json_path = os.path.join(json_folder, json_file)

            # Load JSON data
            with open(json_path, 'r') as file:
                json_data = json.load(file)

            # Preprocess JSON data
            json_data = preprocess_json_data(json_data)

            # Convert JSON to XML
            xml_data = convert_json_to_xml_v2(json_data, gpt4o_url, gpt4o_key)

            # Save XML output
            xml_filename = f"{os.path.splitext(json_file)[0]}.xml"
            xml_path = os.path.join(xml_output_folder, xml_filename)
            with open(xml_path, 'w') as xml_file:
                xml_file.write(xml_data)
            print(f"Saved XML: {xml_path}")

def preprocess_json_data(json_data):
    """
    Preprocesses JSON data and extracts all possible fields for XML conversion.
    Extracts patient info, all key-value pairs, all lines, and all table cells as fields.
    """
    import re
    
    # Ensure 'fields' key exists
    if 'fields' not in json_data:
        json_data['fields'] = {}

    # Extract all key-value pairs
    for k, v in json_data.get('key_value_pairs', {}).items():
        field_name = k.strip().replace(':', '').replace(' ', '_').lower()
        json_data['fields'][field_name] = {'content': v.strip()}

    # Extract all lines from all pages
    for page in json_data.get('pages', []):
        for idx, line in enumerate(page.get('lines', [])):
            field_name = f'page{page.get("page_number", 1)}_line{idx+1}'
            json_data['fields'][field_name] = {'content': line.strip()}

    # Extract all table cells
    for table in json_data.get('tables', []):
        for idx, cell in enumerate(table.get('cells', [])):
            field_name = f'tablecell_{idx+1}'
            json_data['fields'][field_name] = {'content': cell.get('content', '').strip()}

    # (Optional) Still try to extract patient info with regex for backward compatibility
    all_content = ''
    if 'content' in json_data:
        all_content += json_data['content'] + ' '
    for page in json_data.get('pages', []):
        if 'lines' in page:
            all_content += ' '.join(page['lines']) + ' '
    for table in json_data.get('tables', []):
        if 'cells' in table:
            for cell in table['cells']:
                if 'content' in cell:
                    all_content += cell['content'] + ' '
    # ...existing code for regex extraction if needed...
    return json_data

def convert_json_to_xml_dynamic(json_data):
    """
    Dynamically generates XML from JSON data, including all fields as <label> elements.
    """
    import xml.etree.ElementTree as ET
    from xml.dom import minidom

    root = ET.Element('root')
    general = ET.SubElement(root, 'general', {
        'app_version': '3.1',
        'lng': 'de',
        'name': json_data.get('form_name', 'Generic Medical Form'),
        'special_type': '',
        'type': 'patient',
        'uuid': json_data.get('uuid', 'GENERIC-UUID'),
        'version': '1.0'
    })
    ET.SubElement(root, 'rules')
    form = ET.SubElement(root, 'form', {
        'export_positives_only': 'true',
        'name': '',
        'pageNumbers': 'true',
        'pageNumbersHidden': 'false',
        'pageNumbersPos': 'bottom_center',
        'pageNumbersType': 'text',
        'pdf_drawing': 'false',
        'pdf_only': 'true',
        'ref': json_data.get('form_ref', 'GENERIC-FORM-REF'),
        'subtitle': '',
        'title': json_data.get('form_title', json_data.get('form_name', 'Generic Medical Form')),
        'type': 'patient'
    })
    signatures = ET.SubElement(form, 'signatures')
    ET.SubElement(signatures, 'signature', {
        'date': 'true',
        'location': 'true',
        'ref': 'GENERIC-SIGNATURE-REF',
        'title': 'Unterschrift der Patientin / des Patienten',
        'type': 'patient'
    })
    page = ET.SubElement(form, 'page', {
        'ref': 'GENERIC-PAGE-REF',
        'title': json_data.get('form_title', json_data.get('form_name', 'Generic Medical Form'))
    })
    # Add all fields as <label> elements
    for field, value in json_data.get('fields', {}).items():
        label = ET.SubElement(page, 'label', {
            'name': field,
            'title': f"§{value.get('content', '')}§"
        })
    ET.SubElement(root, 'localisation')
    # Pretty print
    xml_str = ET.tostring(root, encoding='utf-8')
    parsed = minidom.parseString(xml_str)
    return parsed.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')

def main():
    # Initialize the Azure Content Understanding Client
    endpoint = os.getenv('AZURE_CONTENT_UNDERSTANDING_ENDPOINT', 'https://ai-t-kpanchal-5150.services.ai.azure.com/')
    api_version = "2025-05-01-preview"
    subscription_key = os.getenv('AZURE_CONTENT_UNDERSTANDING_KEY')
    
    if not subscription_key:
        raise ValueError("AZURE_CONTENT_UNDERSTANDING_KEY is not defined. Please check your .env file.")

    client = AzureContentUnderstandingClient(
        endpoint=endpoint,
        api_version=api_version,
        subscription_key=subscription_key
    )    # Define input and output folders for JSON and XML
    json_folder = "json_output/"
    xml_output_folder = "xml_output/"

    # Ensure directories exist
    os.makedirs(json_folder, exist_ok=True)
    os.makedirs(xml_output_folder, exist_ok=True)

    # GPT-4o API details
    gpt4o_url = os.getenv('GPT4O_URL')
    gpt4o_key = os.getenv('GPT4O_KEY')

    # Ensure GPT-4o URL and key are loaded from the .env file
    if not gpt4o_url:
        raise ValueError("GPT-4o URL is not defined. Please check your .env file (GPT4O_URL).")
    if not gpt4o_key:
        raise ValueError("GPT-4o key is not defined. Please check your .env file (GPT4O_KEY).")

    print("Starting PDF processing workflow...")
    
    # Get list of JSON files
    json_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]
    if not json_files:
        print("No JSON files found in the json_output folder.")
        return
    
    print(f"Found {len(json_files)} JSON file(s) to process:")
    for json_file in json_files:
        print(f"  - {json_file}")
    print()

    # Process JSON files
    for json_file in json_files:
        print(f"Processing: {json_file}")
        json_path = os.path.join(json_folder, json_file)

        try:            # Load JSON data
            with open(json_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)

            # Preprocess JSON data
            json_data = preprocess_json_data(json_data)

            # Convert JSON to XML using dynamic approach
            xml_data = convert_json_to_xml_dynamic(json_data)

            # Save XML output
            xml_filename = f"{os.path.splitext(json_file)[0]}.xml"
            xml_path = os.path.join(xml_output_folder, xml_filename)
            with open(xml_path, 'w', encoding='utf-8') as xml_file:
                xml_file.write(xml_data)
            print(f"✅ Successfully saved XML: {xml_path}")
            
        except Exception as e:
            print(f"❌ Error processing {json_file}: {str(e)}")
            continue

    print(f"\n🎉 Processing complete! Check the '{xml_output_folder}' folder for XML outputs.")

if __name__ == "__main__":
    main()

