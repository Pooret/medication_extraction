# main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import uuid
import tempfile
import shutil

import os
import argparse
from pdf_parser import extract_text_from_pdf
from llm_extraction import extract_medications
from verifier import validate_medication_api
from preprocessing import preprocess_text
from output_generation import generate_json_output, generate_markdown_output

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
# Store results temporarily (in production, you'd use a database)
results_store = {}


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

@app.post("/extract")
async def extract_medications_from_pdf(file: UploadFile = File(...)):

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    job_id = str(uuid.uuid4())

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_filepath = temp_file.name

        # Step 1: Extract text from PDF
        extracted_text = extract_text_from_pdf(temp_filepath)
        if not extracted_text:
            print("Could not extract text from the document. Skipping.")
            return

        # 2. Clean and preprocess text
        cleaned_text = preprocess_text(extracted_text)

        # 3. Extract medications using the LLM
        extracted_meds = extract_medications(cleaned_text)
        if not extracted_meds:
            results_store[job_id] = {
                "status": "completed",
                "filename": file.filename,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "medications": [],
                "message": "No medications found"
            }
        else:
            # 4. Verify each medication against the RxNorm API
            final_med_data = []
            for med in extracted_meds:
                final_med_data.append(validate_medication_api(med))

            results_store[job_id] = {
                "status": "completed",
                "filename": file.filename,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "medications": final_med_data,
                "total_medications": len(final_med_data),
                "validated_count": sum(1 for med in final_med_data if med.get('validated', False))
            }

        os.unlink(temp_filepath)

        return {
            "job_id": job_id,
            "status": "completed",
            "message": "PDF processed successfully",
            "filename": file.filename
        }
    except Exception as e:
        if 'temp_filepath' in locals():
            try:
                os.unlink(temp_filepath)
            except:
                pass
            
        results_store[job_id] = {
            "status": "error",
            "filename": file.filename,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }
        
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
@app.get("/results/{job_id}")
async def get_results(job_id:str):
        if job_id not in results_store:
            raise HTTPException(status_code=404, detail=f"Job ID {job_id} not found")
        
        return results_store[job_id]

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