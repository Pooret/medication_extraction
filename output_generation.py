# output_generation.py

import json

def generate_json_output(medication_data: list, filepath: str):
    """
    Saves the final, validated medication data to a structured JSON file.

    Args:
        medication_data: A list of dictionaries, where each dict is a medication.
        filepath: The path to save the output JSON file (e.g., 'medications.json').
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(medication_data, f, indent=2)
        print(f"Successfully created JSON file: {filepath}")
    except Exception as e:
        print(f"Error creating JSON file: {e}")


def generate_markdown_output(medication_data: list, filepath: str):
    """
    Formats the final, validated medication data into a human-readable
    Markdown file.

    Args:
        medication_data: A list of dictionaries, where each dict is a medication.
        filepath: The path to save the output Markdown file (e.g., 'medications.md').
    """
    try:
        lines = ["### Extracted Medications and Dosages\n"]
        if not medication_data:
            lines.append("No medications were extracted.")
        else:
            for med in medication_data:
                lines.append(f"- **Medication**: {med.get('medication', 'N/A')}")
                lines.append(f"  **Dosage**: {med.get('dosage', 'N/A')}")
                lines.append(f"  **Validated**: {med.get('validated', False)}")
                
                # Format the additional_information dictionary into a clean string
                add_info = med.get('additional_information', {})
                info_str = json.dumps(add_info) if add_info else "None"
                lines.append(f"  **Additional Information**: {info_str}\n")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        print(f"Successfully created Markdown file: {filepath}")
    except Exception as e:
        print(f"Error creating Markdown file: {e}")
