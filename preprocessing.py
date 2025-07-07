# preprocessing.py
import re

def preprocess_text(text: str) -> str:
    """
    Clean and normalize raw text extracted from PDFs.
    """
    if not text:
        return ""

    # Normalize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Fix hyphenated line breaks like "medica-\ntion" -> "medication"
    text = re.sub(r"-\s*\n\s*", "", text)

    # Collapse multiple spaces and newlines
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    return text.strip()

if __name__ == "__main__":
    text = """
    Mr. Ruiz, a 47-year-old male, presents as a transfer from an outside hospital for management of
    mediastinitis and persistent Group B Streptococcus (GBS) and Methicillin-resistant Staphylococcus aureus
    (MRSA) bacteremia. Onset: The patient initially presented to the outside hospital on ___ with a 6-day
    history of generalized malaise, nausea, vomiting, diarrhea, and intermittent chest discomfort. Location:
    The patient was found to have a large fluid collection in the mediastinum at the sternotomy site, with
    concern for extension to the pericardium. Duration: Symptoms had been present for approximately 6 days
    prior to initial presentation. Character: The patient reported generalized malaise and chest discomfort.
    """

    preprocessed_text = preprocess_text(text)
    print(preprocessed_text)
