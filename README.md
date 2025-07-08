# Medication Extraction from Medical Reports

This project provides a robust, automated pipeline for extracting medication information from unstructured PDF medical reports. It leverages Large Language Models (LLMs) for intelligent text recognition and data extraction, and verifies the extracted medications against the official NIH RxNorm API to ensure clinical accuracy.

## 1. My Approach to Solving the Problem

I designed the solution as a modular pipeline, breaking the complex problem into five distinct, manageable steps. Each step is handled by a dedicated Python module, ensuring the code is clean, maintainable, and easy to understand.

**The 5-Step Pipeline:**

1.  **Hybrid PDF Parsing (`pdf_parser.py`):** The process begins with universal text extraction. Recognizing that medical reports can be either text-based PDFs or scanned images, the parser first attempts a direct text extraction with `pdfplumber`. If a page yields little or no text (indicating it's an image), it automatically falls back to a powerful multimodal vision model (`gemini-1.5-pro`) to perform Optical Character Recognition (OCR). This hybrid approach ensures that virtually any PDF report can be processed without failure.

2.  **Text Preprocessing (`preprocessing.py`):** Raw extracted text is often messy. This module normalizes the text by fixing common OCR and formatting artifacts, such as inconsistent line breaks, hyphenated words at line endings, and redundant whitespace. This cleaning step provides a clean, coherent input for the LLM.

3.  **LLM-Powered Extraction (`llm_extraction.py`):** The cleaned text is then passed to a fine-tuned Gemini model (`gemini-2.5-flash`). By using `langchain` with Pydantic models, I enforce a structured JSON output from the LLM. This is a critical design choice that guarantees the data sent to the next step is always in the correct format, making the entire system more reliable and eliminating the need for fragile manual parsing of the LLM's response.

4.  **External Verification (`verifier.py`):** Each extracted medication is validated against the NIH RxNorm API. A key challenge here is that extracted medication names can be messy (e.g., "Metoprolol Succinate XL 25mg"). To solve this, I implemented a **progressive validation** function. It intelligently checks for the longest valid medication name recognized by the API (first checking "Metoprolol", then "Metoprolol Succinate"). This method is far more resilient and accurate than a simple exact-match lookup.

5.  **Output Generation (`output_generation.py`):** Finally, the validated data is formatted and saved into the two required outputs: a structured `JSON` file for machine readability and a clean `Markdown` file for human review.

## 2. Core Assumptions & Scope

To deliver a focused and effective solution, I made the following key assumptions about the project's scope:

* **Focus on Actionable, Post-Discharge Medications:** The primary goal is to extract the final medication list the patient must follow at home. This is the most critical information for patient safety and continuity of care.
* **Explicitly Ignore Transitory & Discontinued Meds:** The system is intentionally designed to filter out medications administered only *during* the hospital stay and any medications the patient was explicitly told to *stop* taking.
* **Include General Clinical Instructions:** Important non-specific instructions (e.g., "take a daily steroid inhaler," "continue with ACE inhibitors") are captured as they represent actionable clinical advice.
* **Primacy of the Discharge List:** In cases of conflicting information within a report, the "Medications at Discharge" or equivalent section is considered the single source of truth.

## 3. Prompt Design and Model Selection

The quality of the extraction hinges on the quality of the prompt and the capability of the model.

### Prompt Engineering

My final prompt in `llm_extraction.py` was refined based on several key principles:
* **Role-Playing:** Assigning the LLM the role of an "expert clinical data extraction assistant" primes it for higher accuracy.
* **Clear Positive and Negative Constraints:** The prompt is highly specific, listing the exact sections to focus on ("Medications At Discharge," "Patient Instructions") while explicitly instructing the model to *ignore* irrelevant sections ("Hospital Course," "Medications Administered"). This significantly reduces noise.
* **Detail-Oriented Instructions:** The prompt directs the model to correct common misspellings (e.g., "Cefodoxime" -> "Cefpodoxime") and capture general medication classes, which are often missed by simpler extraction rules.
* **Output Structuring:** By using LangChain's `with_structured_output` feature, the model is forced to return valid JSON conforming to a Pydantic model, ensuring downstream reliability.

### Model Evaluation and Choice

To empirically select the best model, I used the **`promptfoo`** framework to evaluate 8 different prompts against a suite of test cases, including several difficult edge cases. I benchmarked models from OpenAI, Google, and Anthropic.

The results were clear: while `gpt-4o-mini` performed well and could achieve 100% accuracy on some tests, its performance was not consistently reproducible across all edge cases. **`gemini-2.5-flash` demonstrated higher overall accuracy and, critically, greater consistency in its structured output.** For a clinical application where accuracy and reliability are paramount, consistency was the deciding factor, making Gemini the optimal choice for this task.

## 4. Challenges and Solutions

* **Challenge:** Handling heterogeneous PDF formats (text-based vs. scanned images).
    * **Solution:** The **hybrid text/OCR parser** in `pdf_parser.py` automatically detects the page type and applies the appropriate extraction method, creating a single, robust ingestion point.
* **Challenge:** Validating messy or misspelled medication names against a strict API.
    * **Solution:** This was addressed with a two-pronged approach. First, the LLM is prompted to correct misspellings. Second, the **progressive validation** logic in `verifier.py` intelligently finds the most specific valid name, dramatically improving the success rate of API verification.
* **Challenge:** Ensuring the LLM returns data in a usable, consistent format.
    * **Solution:** Using `langchain` with Pydantic models (`with_structured_output`) completely bypasses the problem of parsing unpredictable LLM text outputs. It forces the model's response into a reliable, pre-defined schema, making the entire pipeline more resilient.

## 5. Future Enhancements & Scope Limitations

While the current solution is robust and meets all requirements, here are several enhancements that could be implemented in a future iteration to further improve its capabilities:

* **Advanced Preprocessing:** Implement a preprocessing step to expand common medical abbreviations (e.g., "PO" to "by mouth", "QID" to "four times daily") and remove redundant boilerplate phrases. This would enrich the extracted data and improve the extraction for the LLM. It's possible that less advanced model than gemini-2.5-flash would have been sufficient given better preprocessing.
* **Dedicated Post-OCR Spell-Checking:** While the LLM is prompted to correct misspellings, OCR can sometimes produce errors that are too significant for the model to fix. A dedicated spell-checking layer (using a library like `pyspellchecker` with a custom medical dictionary) after OCR could further improve data quality before it reaches the extraction model.
* **Full Strength and Route Validation:** The current verification confirms the medication's existence. A more advanced version could leverage the RxNorm API further to validate that the extracted **dosage strength** (e.g., "10mg") is a commercially marketed strength for that drug and validate the **route of administration**.
* **Broader Entity Extraction:** The pipeline could be expanded to extract other valuable clinical entities, such as diagnoses, allergies, or lab values, by creating new Pydantic models and adjusting the LLM prompt.

## 6. How to Run the Code

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