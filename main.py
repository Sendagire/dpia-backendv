import os
from fastapi import FastAPI, HTTPException
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
    prompt = f"""
    Act as a Privacy Risk Assessor. Review the following project:
    - Name: {data.project_name}
    - Description: {data.project_desc}
    - Subjects: {data.data_subjects}
    - Data: {data.data_collected}
    - Retention: {data.retention}
    - Third Parties: {data.third_parties}
    
    Identify ALL relevant privacy risks. For EACH risk, provide: 1. Risk Description. 2. Recommended Mitigation.
    Present this as a clean list. No tables.
    """
    try:
        # Using Claude 3.5 Sonnet
        response = completion(model="claude-3-5-sonnet-20241022", messages=[{"role": "user", "content": prompt}])
        return {"status": "success", "risks": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-report")
async def generate_final_report(data: FinalReportRequest):
    prompt = f"""
    Act as a Senior Privacy Counsel. Write a final Data Protection Impact Assessment (DPIA).
    The initial assessment identified: {data.identified_risks}
    
    Write the final DPIA report structured exactly like this using Markdown:
    ## 1. Executive Summary
    ## 2. Scope of Processing
    ## 3. Privacy Risks, Mitigation & Required Evidence
    Draw a Markdown Table: | Privacy Risk | Recommended Mitigation | Evidence Required for Audit |
    ## 4. Final Risk Rating & Justification
    
    DO NOT use "AI" or "Artificial Intelligence". Read as an internal Privacy Team document. Use **bold text** for emphasis.
    """
    try:
        response = completion(model="claude-3-5-sonnet-20241022", messages=[{"role": "user", "content": prompt}])
        ai_report = response.choices[0].message.content
        
        doc = Document()
        # Word formatting... (Keep your existing Word formatting logic here)
        doc.add_paragraph('Data Protection Impact Assessment', style='Title')
        doc.add_paragraph(ai_report)
        
        file_name = f"/tmp/{data.project_name.replace(' ', '_')}_Final_DPIA.docx"
        doc.save(file_name)
        return FileResponse(path=file_name, filename=f"{data.project_name.replace(' ', '_')}_Final_DPIA.docx", media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except Exception as e:
        return {"status": "error", "message": str(e)}
