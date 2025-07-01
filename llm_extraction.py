# llm_extraction.py

import os
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class Medication(BaseModel):
    """Pydantic model for a single medication."""
    medication: str = Field(description="The name of the drug, corrected for any misspellings.")
    dosage: str = Field(description="A single string that includes all dosage and administration instructions.")
    validated: bool = Field(default=False, description="Flag indicating if the medication was validated.")
    additional_information: Dict[str, Any] = Field(default_factory=dict, description="Supplementary data like RxCUI or errors.")

class MedicationList(BaseModel):
    """Pydantic model for a list of medications."""
    medications: List[Medication]

def extract_medications(full_text: str) -> List[Medication]:
    """
    Uses a structured LLM call to extract medications from medical text.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        api_key=os.getenv("GEMINI_API_KEY")
    )
    structured_llm = llm.with_structured_output(MedicationList)

    extraction_prompt = f"""
    You are an expert clinical data extraction assistant. Your task is to identify and extract ONLY the medications the patient has been prescribed to take *after* hospital discharge from the provided "Medical Report Text".

    - Focus on sections titled "Medications At Discharge", "Discharge Medications", "Patient Instructions", and the "Plan" within the "Observation and Plan" section.
    
    - It is critical that you find all medications. This includes general medication classes mentioned in the 'Plan' section (like 'beta-blockers' and 'ACE inhibitors') AND items mentioned in the 'Patient Instructions' (like 'steroid inhaler'). These are just as important as the named drugs. If medications are mispelled, spell thim correctly (change the mispelled "Cefodoxime" to the antibiotic "Cefpodoxime")
    
    - **For medications with multiple parts to their dosage or frequency (like a sublingual dose AND an IV drip), you MUST combine all parts into the final dosage string.**
    
    - Explicitly IGNORE medications mentioned only in "Hospital Course", "Medications Administered" during the stay, or those the patient is told to "Stop taking".

    Your output MUST be a single, valid JSON array of objects, with no other text, explanations, or markdown.

    Here is an example of the required output format for a complex case:
    [{{"medication": "Nitroglycerin", "dosage": "0.4 mg sublingually, IV drip As needed, continuous"}}]

    Medical Report Text:
    {full_text}
    ---
    """
    
    response = structured_llm.invoke(extraction_prompt)
    return response.medications

if __name__ == '__main__':
    sample_text = """
    Patient Name: White, Alan Joseph
    
    Hospital Course
    Alan White was immediately started on a heparin drip and given a loading dose of clopidogrel. During his stay, he was managed with IV diltiazem.
    
    Medications Administered
    Medication           Dosage         Frequency
    Aspirin              81 mg          Daily
    Metoprolol           25 mg          Twice daily
    Egexbede             1 mg           Daily
    
    Patient Instructions
    Stop taking Hydrochlorothiazide and simvastatin.
    Continue taking aspirin, Plavix, and diltiazem.
    """

    response = extract_medications(sample_text)
    print(response)
