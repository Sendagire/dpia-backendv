import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from litellm import completion
from docx import Document
from docx.shared import Pt, RGBColor

app = FastAPI(title="DPIA Enterprise API")

# Ensure this matches your CORS requirements
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

@app.post("/api/analyze")
async def analyze_risks(data: ProjectDetails):
    prompt = f"Identify 3 privacy risks for: {data.project_name}. Provide Description and Mitigation."
    try:
        # Note the comma at the end of the messages line
        response = completion(
            model="anthropic/claude-3-5-sonnet-20240620", 
            messages=[{"role": "user", "content": prompt}],
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        return {"status": "success", "risks": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# (Include your generate-report function here with the SAME api_key fix)
