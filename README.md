# Medication Extraction from Medical Reports

This project is a tool for pulling medication information from unstructured PDF medical reports. It uses LLMs to intelligently find the text and verifies the medications it finds against the NIH RxNorm API.

## 1. My Approach to Solving the Problem

I solved the problem by breaking it into four main steps, with each step handled by its own Python module:

1.  **PDF Parsing (`pdf_parser.py`):** The first part of the pipeline is text extraction. I knew that medical reports could be either normal PDFs with selectable text or scanned images. To handle both, I built a two-step process:
    * It first tries to pull text directly using the `pdfplumber` library.
    * If a page is just an image, the script automatically uses a multimodal vision model to perform Optical Character Recognition (OCR) and read the text from the page. I initially tried Tesseract for OCR but found the vision model was much more accurate, especially with tables.

2.  **LLM-Powered Extraction (`llm_extraction.py`):** The extracted text is then sent to a Gemini-2.5-flash (after testing multiple models) to find the medications. I used `langchain` and Pydantic to force the model to give back a clean, structured JSON every time. This meant I didn't have to write messy code to parse the model's output and could rely on the data being in the right format for the next step.

3.  **External Verification (`verifier.py`):** Next, the script checks each extracted medication against the official NIH RxNorm API to see if it's real. The main challenge was that medication names can be messy (like "Metoprolol Succinate XL"). To solve this, I wrote a **progressive validation** function. It first checks "Metoprolol", then "Metoprolol Succinate", then "Metoprolol Succinate XL", finding the longest possible valid medication name that the API recognizes. This is much more accurate than the original idea of just checking the first word.

4.  **Output Generation (`output_generation.py`):** Finally, the script saves the results in the two required formats: a structured JSON file for computers and a clean Markdown file for people to read.

## 2. Core Assumptions & Scope

To build a useful tool, I had to make a few key decisions about what to include in the extraction. Here’s the scope I decided on:

* **Extract Only What the Patient Needs to Take Home:** I focused on pulling the final list of medications the patient should actually be taking *after* they leave the hospital. This is the most important list for keeping the patient safe.

* **Ignore In-Hospital and Stopped Meds:** This means the script was built to ignore two things: medications only given *during* the hospital stay, and medications the patient was specifically told to *stop* taking.

* **Include General Medication Classes:** The script also grabs general instructions like "steroid inhaler" or "ACE inhibitors," since these are important clinical instructions.

* **The Discharge List is Always Right:** If a report had conflicting medication lists (like what the patient took before vs. after their stay), I treated the "Medications At Discharge" section as the correct and final word.

## 3. Prompt Design and Validation

I designed the final prompt in `llm_extraction.py` using a few key ideas:

* **Role:** I told the LLM to act as an "expert clinical data extraction assistant" to get it in the right mindset.
* **Do's:** The prompt clearly states which sections to look at, like "Medications At Discharge" or "Patient Instructions."
* **Don'ts:** Just as important, it explicitly tells the model what to ignore, like medications from the "Hospital Course" or ones the patient was told to "Stop taking." This was a huge help in getting accurate results.
* **Handling Details:** The prompt asks the model to look for general classes (like "beta-blockers") and to fix common misspellings it finds.
* **Structured Output:** By using LangChain's structured output feature, the model *has* to return valid JSON, which makes the whole system more stable.

To make sure I was using the best possible prompt, I used **`promptfoo`** to test 8 different prompt ideas against a CSV file of test cases, including some tough edge cases. This let me get real numbers on how well each prompt worked with different models (like GPT, Gemini, and Claude). I picked the one that consistently got the highest score for accuracy and was the most reliable. The results showed that **`gemini-1.5-flash`** with a very specific, few-shot prompt gave the best performance.

## 4. Challenges and Solutions

* **Challenge:** Dealing with different kinds of PDFs (scanned images vs. regular text).
    * **Solution:** The two-step text/OCR process in `pdf_parser.py`. This lets the tool work on any kind of PDF automatically.
* **Challenge:** Validating messy or misspelled medication names.
    * **Solution:** I built a two-part solution. First, the LLM is prompted to fix misspellings during extraction. Second, the **progressive validation** function in `verifier.py` intelligently finds the most specific, correct name to check against the API, making the validation step much more accurate.
* **Challenge:** Getting the LLM to reliably return data in the correct format.
    * **Solution:** Using `langchain` with Pydantic models avoided the headache of trying to parse unpredictable text from the LLM and made the whole process more reliable.

## 5. How to Run the Code

### Setup

First, install the required Python packages:

```bash
pip install -r requirements.txt
```

You will also need to install `poppler`, which is a dependency for the `pdf2image` library.

* **On macOS (using Homebrew):**
    ```bash
    brew install poppler
    ```
* **On Debian/Ubuntu:**
    ```bash
    sudo apt-get install -y poppler-utils
    ```

Next, create a `.env` file in the root of the project directory and add your Gemini API key:

```text
# .env
GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

### Execution

Run the main script from your terminal, providing one or more paths to the PDF files you want to process.

**Syntax:**

```bash
python main.py [PATH_TO_PDF_1] [PATH_TO_PDF_2] ...
```

**Example:**

```bash
python main.py ./test_files/test-report-1.pdf ./test_files/test-report-2.pdf
```

The script will create an `outputs` directory. Inside, a separate folder will be generated for each processed PDF, containing the `_medications.json` and `_medications.md` output files.