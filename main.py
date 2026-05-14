import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import anthropic
from docx import Document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize official Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

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
        # OFFICIAL ANTHROPIC CALL
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"status": "success", "risks": response.content[0].text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
def home():
    return {"message": "✅ DPIA Engine is live and clean!"}
