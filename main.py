# main.py

import os
import argparse
from pdf_parser import extract_text_from_pdf
from llm_extraction import extract_medications
from verifier import validate_medication_api
from output_generation import generate_json_output, generate_markdown_output

def process_report(filepath: str, output_path: str):
    """
    Processes a single medical report PDF to extract, validate, and save medication data.
    """
    try:
        print(f"\n--- Processing file: {os.path.basename(filepath)} ---")

        # 1. Extract text from the PDF
        print("Step 1: Extracting text...")
        extracted_text = extract_text_from_pdf(filepath)
        if not extracted_text:
            print("Could not extract text from the document. Skipping.")
            return

        # 2. Extract medications using the LLM
        print("Step 2: Extracting medications with LLM...")
        extracted_meds = extract_medications(extracted_text)
        if not extracted_meds:
            print("No medications found by the LLM. Skipping.")
            return

        # 3. Verify each medication against the RxNorm API
        print("Step 3: Verifying medications via API...")
        final_med_data = []
        for med in extracted_meds:
            final_med_data.append(validate_medication_api(med))
        
        print("Step 4: Generating output files...")
        # Create a dedicated output directory for the report
        filename = os.path.splitext(os.path.basename(filepath))[0]
        output_dir = os.path.join(output_path, filename)
        os.makedirs(output_dir, exist_ok=True)

        # 4. Generate JSON and Markdown output files
        json_filepath = os.path.join(output_dir, f'{filename}_medications.json')
        md_filepath = os.path.join(output_dir, f'{filename}_medications.md')
        
        generate_json_output(final_med_data, json_filepath)
        generate_markdown_output(final_med_data, md_filepath)
        
        print(f"--- Successfully processed {os.path.basename(filepath)} ---")
        print(f"\n\nYou now can view the outputs in the {output_dir} directory\n\n")

    except Exception as e:
        print(f"An error occurred while processing {filepath}: {e}")

def main():
    """
    Main function to parse command-line arguments and process PDF files.
    """
    parser = argparse.ArgumentParser(
        description="Extracts medications and dosages from unstructured medical PDF reports."
    )
    parser.add_argument(
        "filepaths",
        metavar="FILE",
        type=str,
        nargs='+',
        help="One or more paths to the PDF medical reports to process."
    )
    args = parser.parse_args()

    output_path = os.path.join(os.getcwd(), "outputs")
    os.makedirs(output_path, exist_ok=True)

    for filepath in args.filepaths:
        if os.path.exists(filepath):
            process_report(filepath, output_path)
        else:
            print(f"Error: The file '{filepath}' was not found.")

if __name__ == "__main__":
    main()