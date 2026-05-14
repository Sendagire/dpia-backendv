import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from litellm import completion
from docx import Document
from docx.shared import Pt, RGBColor

app = FastAPI(title="DPIA Enterprise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. ADD THIS HOME ROUTE (Fixes "Not Found" at root) ---
@app.get("/")
def home():
    return {"message": "✅ DPIA Enterprise API is running 24/7!"}

class ProjectDetails(BaseModel):
    project_name: str
    project_desc: str
    data_subjects: str
    data_collected: str
    retention: str
    third_parties: str
    initial_risk: str

class FinalReportRequest(ProjectDetails):
    identified_risks: str

@app.post("/api/analyze")
async def analyze_risks(data: ProjectDetails):
    prompt = f"Identify 3 privacy risks for: {data.project_name}. Provide Description and Mitigation."
    try:
        # --- 2. ADD 'anthropic/' PREFIX HERE ---
        response = completion(
            model="anthropic/claude-3-5-sonnet-20241022", 
            messages=[{"role": "user", "content": prompt}],
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        return {"status": "success", "risks": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-report")
async def generate_final_report(data: FinalReportRequest):
    prompt = f"Act as a Privacy Counsel. Write a DPIA for {data.project_name}. Risks: {data.identified_risks}. Include a Markdown table for Risks | Mitigation | Evidence Required."
    try:
        # --- 2. ADD 'anthropic/' PREFIX HERE ---
        response = completion(
            model="anthropic/claude-3-5-sonnet-20241022", 
            messages=[{"role": "user", "content": prompt}],
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        ai_report = response.choices[0].message.content
        
        doc = Document()
        doc.add_heading('Data Protection Impact Assessment', 0)
        doc.add_paragraph(ai_report)
        
        file_path = f"/tmp/{data.project_name.replace(' ', '_')}_DPIA.docx"
        doc.save(file_path)
        
        return FileResponse(path=file_path, filename="DPIA.docx", media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except Exception as e:
        return {"status": "error", "message": str(e)}
