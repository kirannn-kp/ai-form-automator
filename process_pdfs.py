import os
import fitz  # PyMuPDF
import requests
import json
from PIL import Image
import base64
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Callable, Any, Optional
import time
from pathlib import Path
import xml.etree.ElementTree as ET

# Explicitly load the .env file using its absolute path
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv(dotenv_path=dotenv_path)

print(f"GPT41_KEY: {os.getenv('GPT41_KEY')}")
print(f"GPT4O_KEY: {os.getenv('GPT4O_KEY')}")

class AzureContentUnderstandingClient:
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
    Sends JSON data to GPT-4o for conversion to XML format.
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
                    "You are an AI that converts JSON data into structured XML matching a predefined schema. "
                    "The schema should match the following structure: \n"
                    "<root>\n"
                    "  <general app_version='3.1' lng='de' name='Honorarvereinbarung Kinesiotapetherapie' special_type='' type='patient' uuid='D2D50516-A10E-44A4-AE58-383D4A026092' version='1.0'/>\n"
                    "  <rules/>\n"
                    "  <form export_positives_only='true' name='' pageNumbers='true' pageNumbersHidden='false' pageNumbersPos='bottom_center' pageNumbersType='text' pdf_drawing='false' pdf_only='true' ref='9A37547F-B21F-41EE-9811-91CB22C34E89' subtitle='' title='Honorarvereinbarung Kinesiotapetherapie' type='patient'>\n"
                    "    <signatures>\n"
                    "      <signature date='true' location='true' ref='41F94F08-AD4A-48F8-8F8A-4EE8129CFAE6' title='Unterschrift der Patientin / des Patienten' type='patient'/>\n"
                    "    </signatures>\n"
                    "    <page ref='40B08450-1423-47DC-BB02-1ED1C782C771' title='Honorarvereinbarung'>\n"
                    "      <label align='left' bottom_space='2' font='subheader' name='Text' ref='B686AFA1-4B8D-4A3C-8F7C-9FE70761A079' title='§{pat_complete}§' top_space='30'/>\n"
                    "      <!-- Additional labels omitted for brevity -->\n"
                    "    </page>\n"
                    "  </form>\n"
                    "  <localisation/>\n"
                    "</root>\n"
                    "Ensure the XML output replicates this structure accurately, including all attributes and nested elements. "
                    "Validate the XML to ensure it is well-formed and matches the expected structure."
                )
            },
            {
                "role": "user",
                "content": f"Please convert the following JSON data into XML with the expected structure:\n{json.dumps(json_data, indent=4)}"
            }
        ]
    }

    response = requests.post(gpt4o_url, headers=headers, json=data)
    response.raise_for_status()
    print("Successfully converted JSON to XML.")
    return response.json()["choices"][0]["message"]["content"]

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
    Preprocesses JSON data to ensure it contains all required fields for XML generation.
    """
    # Ensure 'fields' key exists
    if 'fields' not in json_data:
        json_data['fields'] = {}

    # Add missing fields with default or inferred values
    json_data['fields']['pat_complete'] = json_data['fields'].get('pat_complete', 'John Doe')
    json_data['fields']['pat_dob'] = json_data['fields'].get('pat_dob', '01.01.1980')
    json_data['fields']['pat_street'] = json_data['fields'].get('pat_street', '123 Main Street')
    json_data['fields']['pat_postalcode'] = json_data['fields'].get('pat_postalcode', '12345')
    json_data['fields']['pat_city'] = json_data['fields'].get('pat_city', 'Sample City')

    # Ensure markdown content is properly formatted
    if 'markdown' in json_data:
        json_data['markdown'] = json_data['markdown'].replace('\u00c4', 'Ä').replace('\u00fc', 'ü').replace('\u00f6', 'ö')

    return json_data

def main():
    # Initialize the Azure Content Understanding Client
    endpoint = "https://ai-t-kpanchal-5150.services.ai.azure.com/"
    api_version = "2025-05-01-preview"
    subscription_key = "7VlgDMG3kaHBNAZfSHOgBZEAMKs9KbDrYPNW7pDBOV9xw0lnHbC0JQQJ99BFACfhMk5XJ3w3AAAAACOG0mzh"

    client = AzureContentUnderstandingClient(
        endpoint=endpoint,
        api_version=api_version,
        subscription_key=subscription_key
    )

    # Define input and output folders for JSON and XML
    json_folder = "json_output/"
    xml_output_folder = "xml_output/"

    # GPT-4o API details
    gpt4o_url = "https://AIAgent-openai02.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"
    gpt4o_key = os.getenv('GPT4O_KEY')

    # Ensure GPT-4o key is loaded from the .env file
    if not gpt4o_key:
        raise ValueError("GPT-4o key is not defined. Please check your .env file.")

    # Process JSON files
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
            with open(xml_path, 'w', encoding='utf-8') as xml_file:
                xml_file.write(xml_data)
            print(f"Saved XML: {xml_path}")

if __name__ == "__main__":
    main()
