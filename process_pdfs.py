import os
import fitz  # PyMuPDF
import requests
import json
from PIL import Image
import base64
from dotenv import load_dotenv

# Explicitly load the .env file using its absolute path
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv(dotenv_path=dotenv_path)

print(f"GPT41_KEY: {os.getenv('GPT41_KEY')}")
print(f"GPT4O_KEY: {os.getenv('GPT4O_KEY')}")

def convert_pdf_to_images(pdf_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.endswith('.pdf'):
            pdf_path = os.path.join(pdf_folder, pdf_file)
            pdf_document = fitz.open(pdf_path)

            for page_number in range(len(pdf_document)):
                page = pdf_document[page_number]
                pix = page.get_pixmap()
                image_filename = f"{os.path.splitext(pdf_file)[0]}_page_{page_number + 1}.jpeg"
                image_path = os.path.join(output_folder, image_filename)
                pix.save(image_path)
                print(f"Saved image: {image_path}")

def send_image_to_gpt41(image_path, gpt41_url, gpt41_key):
    # Encode the image in Base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    headers = {
        'api-key': gpt41_key,
        'Content-Type': 'application/json'
    }
    data = {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Please extract all relevant text and metadata from this image and structure it into a detailed Markdown table. "
                    "Ensure the table includes all fields, labels, and their associated values as they appear in the form. "
                    "Focus on accurately capturing the structure and content of the form titled 'Honorarvereinbarung Eventrekorder'. "
                    "Avoid placeholder or fabricated data and ensure all extracted content matches the original form. "
                    "If a field is empty in the form, represent it as an empty tag in the XML."
                )
            },
            {
                "role": "user",
                "content": f"data:image/jpeg;base64,{base64_image}"
            }
        ]
    }

    try:
        response = requests.post(gpt41_url, headers=headers, json=data)
        response.raise_for_status()
        print("Successfully processed image to Markdown table.")
        return response.json()  # Return the full JSON response
    except requests.exceptions.RequestException as e:
        print(f"Failed to process image. Error: {e}")
        if response is not None:
            print("Response Content:", response.text)

        # Fallback to OCR
        print("Falling back to OCR for text extraction.")
        try:
            from pytesseract import image_to_string
            from PIL import Image

            ocr_text = image_to_string(Image.open(image_path))
            print("OCR extracted text:", ocr_text)
            return {"choices": [{"message": {"content": ocr_text}}]}  # Simulate GPT response
        except Exception as ocr_error:
            print(f"OCR failed: {ocr_error}")
        return None

def send_image_to_gpt41_with_original_xml(image_path, gpt41_url, gpt41_key, original_xml):
    # Encode the image in Base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    headers = {
        'api-key': gpt41_key,
        'Content-Type': 'application/json'
    }
    data = {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Please extract all relevant text and metadata from this image and structure it into a detailed Markdown table. "
                    "Ensure the table includes all fields, labels, and their associated values as they appear in the form. "
                    "Focus on accurately capturing the structure and content of the form titled 'Honorarvereinbarung Eventrekorder'. "
                    "Use the following XML as a reference for the expected structure and content: \n" + original_xml + "\n"
                    "Avoid placeholder or fabricated data and ensure all extracted content matches the original form. "
                    "If a field is empty in the form, represent it as an empty tag in the XML."
                )
            },
            {
                "role": "user",
                "content": f"data:image/jpeg;base64,{base64_image}"
            }
        ]
    }

    try:
        response = requests.post(gpt41_url, headers=headers, json=data)
        response.raise_for_status()
        print("Successfully processed image to Markdown table using original XML as reference.")
        return response.json()  # Return the full JSON response
    except requests.exceptions.RequestException as e:
        print(f"Failed to process image. Error: {e}")
        if response is not None:
            print("Response Content:", response.text)
        return None

#comment extra
def send_image_to_gpt41_with_debug(image_path, gpt41_url, gpt41_key, original_xml):
    # Encode the image in Base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    headers = {
        'api-key': gpt41_key,
        'Content-Type': 'application/json'
    }
    data = {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Please extract all relevant text and metadata from this image and structure it into a detailed Markdown table. "
                    "Ensure the table includes all fields, labels, and their associated values as they appear in the form. "
                    "Focus on accurately capturing the structure and content of the form titled 'Honorarvereinbarung Eventrekorder'. "
                    "Use the following XML as a reference for the expected structure and content: \n" + original_xml + "\n"
                    "Avoid placeholder or fabricated data and ensure all extracted content matches the original form. "
                    "If a field is empty in the form, represent it as an empty tag in the XML."
                )
            },
            {
                "role": "user",
                "content": f"data:image/jpeg;base64,{base64_image}"
            }
        ]
    }

    try:
        response = requests.post(gpt41_url, headers=headers, json=data)
        response.raise_for_status()
        print("Successfully processed image to Markdown table using original XML as reference.")
        markdown_content = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        debug_extracted_data(markdown_content)  # Debugging step
        return markdown_content
    except requests.exceptions.RequestException as e:
        print(f"Failed to process image. Error: {e}")
        if response is not None:
            print("Response Content:", response.text)
        return None

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
        import xml.etree.ElementTree as ET
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

def main():
    pdf_folder = "examplePdf"
    image_output_folder = "converted_images"
    gpt41_url = "https://AIAgent-openai02.openai.azure.com/openai/deployments/gpt-4.1-2/chat/completions?api-version=2025-01-01-preview"
    gpt41_key = os.getenv("GPT41_KEY")
    gpt4o_url = os.getenv("GPT4O_URL", "https://AIAgent-openai02.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview")
    gpt4o_key = os.getenv("GPT4O_KEY")

    if not gpt41_key or not gpt4o_key:
        print("Error: API keys for GPT-4.1 or GPT-4o are not set in environment variables.")
        exit(1)

    # Step 1: Convert PDFs to images
    convert_pdf_to_images(pdf_folder, image_output_folder)

    # Step 2: Process images with GPT-4.1 for Markdown table generation
    for image_file in os.listdir(image_output_folder):
        if image_file.endswith('.jpeg'):
            image_path = os.path.join(image_output_folder, image_file)
            markdown_response = send_image_to_gpt41(image_path, gpt41_url, gpt41_key)

            if markdown_response:
                markdown_content = markdown_response.get('choices', [{}])[0].get('message', {}).get('content', '')

                # Step 3: Convert Markdown table to XML with GPT-4o
                xml_response = send_markdown_to_gpt4o(markdown_content, gpt4o_url, gpt4o_key)

                if xml_response:
                    xml_content = xml_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                    xml_filename = f"{os.path.splitext(image_file)[0]}.xml"
                    xml_path = os.path.join("xml_output", xml_filename)

                    # Step 4: Validate and save XML
                    validate_and_save_xml(xml_content, xml_path)

if __name__ == "__main__":
    main()
