# verifier.py

import requests
import re

def validate_medication_api(medication_object) -> dict:
    """
    Validates a medication name using a progressive search against the NIH RxNorm API.
    It finds the longest possible valid medication name from the start of the string.
    Returns a dictionary with validation status and additional info.
    """
    output_dict = {
        "medication": medication_object.medication,
        "dosage": medication_object.dosage,
        "validated": False,
        "additional_information": {}
    }

    # This will store the most recent successful validation result.
    last_successful_match = {}

    # Clean the name by removing parentheticals and split it into words
    cleaned_name = re.sub(r'\(.*\)', '', medication_object.medication).strip()
    words = cleaned_name.split(' ')

    # Progressively build the search term word by word
    for i in range(len(words)):
        # Create the current term, e.g., "Metoprolol", then "Metoprolol Succinate"
        current_term = " ".join(words[:i + 1])

        base_url = "https://rxnav.nlm.nih.gov/REST/rxcui.json"
        params = {'name': current_term}

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get('idGroup', {}).get('rxnormId'):
                # SUCCESS: This term is valid. Store it as our best match so far and continue.
                last_successful_match = {
                    'rxcui': data['idGroup']['rxnormId'][0],
                    'matched_term': current_term
                }
            else:
                # FAILURE: This term is invalid. The previous one was the best we could do.
                # Stop searching for longer terms.
                break

        except requests.exceptions.RequestException as e:
            print(f"  - API validation error for '{current_term}': {e}")
            output_dict['additional_information']['validation_error'] = f"API request failed: {e}"
            # If the API itself fails, we can't continue, so return with the error.
            return output_dict

    # After the loop, check if we ever had a successful match
    if last_successful_match:
        # We found at least one valid prefix. Use the last (most specific) one.
        output_dict['validated'] = True
        output_dict['additional_information'] = last_successful_match
    else:
        # We never found a valid match, even for the first word.
        output_dict['additional_information']['validation_error'] = "Medication not found in RxNorm."

    return output_dict

if __name__ == '__main__':
    from pdf_parser import extract_text_from_pdf
    from llm_extraction import extract_medications
    filepath = "/Users/tylerpoore/Workspace/projects/takehome_cascala/medication_extraction/test_files/test-report-3.pdf"

    full_report_text = extract_text_from_pdf(filepath)

    if full_report_text:
        extracted_meds = extract_medications(full_report_text)
    
    if extracted_meds:
        medications = []
        for med_object in extracted_meds:
            medications.append(validate_medication_api(med_object))
        
    for medication in medications:
        print(medication)
        
