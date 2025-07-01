# pdf_parser.py

import io
import os
import base64
import pdfplumber
from pdf2image import convert_from_path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

def transcribe_image(img) -> str:
    """
    Performs OCR on a single image using a multimodal LLM.
    """
    llm = ChatGoogleGenerativeAI(
        model='gemini-1.5-pro-latest',
        temperature=0,
        api_key=API_KEY
    )

    # Convert image to a base64 string
    img_byte_array = io.BytesIO()
    img.save(img_byte_array, format='JPEG')
    img_base64 = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')

    transcription_prompt = """
    Perform a precise and verbatim optical character recognition of the following medical document image.
    Transcribe the text exactly as it appears. Preserve the original line breaks, spacing, and layout as much as possible.
    Do not summarize, interpret, explain, or add any text that is not explicitly in the image.
    Your output should only be the transcribed text from the document.
    """

    message = HumanMessage(
        content=[
            {"type": "text", "text": transcription_prompt},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_base64}"}
        ]
    )
    response = llm.invoke([message])
    return response.content.strip()


def extract_text_from_pdf(filepath: str) -> str:
    """
    Extracts text from a PDF. Uses OCR as a fallback for image-based pages.
    """
    # Pre-convert all pages to images for the OCR fallback
    images = convert_from_path(filepath, dpi=300)

    full_text = ""
    with pdfplumber.open(filepath) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            # If standard text extraction yields little or no text, use OCR
            if page_text and len(page_text.strip()) > 20: # Heuristic to decide if text is meaningful
                full_text += page_text + "\n"
            else:
                print(f"Page {i+1} has no selectable text, falling back to OCR...")
                ocr_text = transcribe_image(images[i])
                full_text += ocr_text + "\n"
    return full_text.strip()



if __name__ == "__main__":
    filepath = "/Users/tylerpoore/Workspace/projects/takehome_cascala/medication_extraction/test_files/test-report-3.pdf"
    extracted_text = extract_text_from_pdf(filepath)
    base_name = os.path.basename(filepath)
    file_name = os.path.splitext(base_name)[0]
    # Create the new markdown file name (e.g., "test-report-2.md")
    output_filepath = f"{file_name}.md"
    with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(extracted_text)
    print(extracted_text)