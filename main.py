# main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import uuid
import tempfile
import shutil
from sqlmodel import Session

import os
import argparse
from pdf_parser import extract_text_from_pdf
from llm_extraction import extract_medications
from verifier import validate_medication_api
from preprocessing import preprocess_text
from output_generation import generate_json_output, generate_markdown_output
from database import get_db, engine
from models import ExtractionJob, create_db_and_tables

app = FastAPI(
    title="Medication Extraction API",
    description="Extract medications from medical PDF reports",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
     create_db_and_tables()

@app.get("/")
async def root():
    return {
        "message": "Medication Extraction API", 
        "version": "1.0.0",
        "endpoints": {
            "extract": "POST /extract - Upload PDF and extract medications",
            "results": "GET /results/{job_id} - Get extraction results",
            "health": "GET /health - Health check"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

@app.post("/extract", response_model=ExtractionJob)
async def extract_medications_from_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    job_id = str(uuid.uuid4())
    temp_filepath = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_filepath = temp_file.name

 # --- Processing Pipeline ---
        extracted_text = extract_text_from_pdf(temp_filepath)
        if not extracted_text:
            raise HTTPException(status_code=404, detail="Could not extract any text from the document.")

        cleaned_text = preprocess_text(extracted_text)
        extracted_meds = extract_medications(cleaned_text)

        final_med_data = []

        if extracted_meds:
            final_med_data = [validate_medication_api(med) for med in extracted_meds]

        new_job = ExtractionJob(
             id = job_id, 
             filename=file.filename,
             medications=final_med_data,
             total_medications=len(final_med_data),
             validated_count = sum(1 for med in final_med_data if med.get('validated', False))
        )

        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        return new_job
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        if temp_file and os.path.exists(temp_filepath):
            os.unlink(temp_filepath)
    
@app.get("/results/{job_id}", response_model=ExtractionJob)
async def get_results(job_id: str, db: Session = Depends(get_db)):
    job_result = db.get(ExtractionJob, job_id)
    if not job_result:
        raise HTTPException(status_code=404, detail=f"Job ID {job_id} not found")
    return job_result

@app.get("/results/{job_id}/json")
async def download_json(job_id:str):
        result = await get_results(job_id)
        if result["status"] != "completed":
            raise HTTPException(status_code=400, detail="Job not completed successfully")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            generate_json_output(result["medications"], temp_file.name)
            temp_filepath = temp_file.name

        return FileResponse(
            temp_filepath,
            media_type='application/json',
            filename=f"medications_{job_id}.json"
        )

@app.get("/results/{job_id}/markdown")
async def download_json(job_id:str):
        result = await get_results(job_id)
        if result["status"] != "completed":
            raise HTTPException(status_code=400, detail="Job not completed successfully")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as temp_file:
            generate_markdown_output(result["medications"], temp_file.name)
            temp_filepath = temp_file.name

        return FileResponse(
            temp_filepath,
            media_type='text/markdown',
            filename=f"medications_{job_id}.md"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)