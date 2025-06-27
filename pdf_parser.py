import pdfplumber
import io
import os
import base64
from pdf2image import convert_from_path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

def transcribe_image(img):
    llm = ChatGoogleGenerativeAI(
        model='gemini-1.5-pro-latest',
        temperature=0,
        api_key=API_KEY
        )
    img_byte_array = io.BytesIO() # create binary array
    img.save(img_byte_array, format='JPEG')
    img_base64 = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')

    transcription_prompt = """
    Perform a precise and verbatim optical character recognition of the following medical document image. Transcribe the text exactly as it appears. Preserve the original line breaks, spacing, and layout as much as possible. Do not summarize, interpret, explain, or add any text that is not explicitly in the image. Your output should only be the transcribed text from the document.
    """

    message = HumanMessage(
        content = [
            {"type": "text", "text": transcription_prompt},
            {"type": "image_url", "image_url":f"data:image/jpeg;base64,{img_base64}"}
        ]
    )
    response = llm.invoke([message])
    return response.content.strip()


def extract_text_with_ocr(filepath):
    images = convert_from_path(filepath, dpi=300)
    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page_number, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text += page_text + "\n"
            else:
                ocr_text = transcribe_image(images[page_number])
                text += ocr_text + "\n"
    return text.strip()


if __name__ == "__main__":
    filepath = "/Users/tylerpoore/Workspace/projects/takehome_cascala/medication_extraction/test_files/test-report-1.pdf"
    extracted_text = extract_text_with_ocr(filepath)
    print(extracted_text)