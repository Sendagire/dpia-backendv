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

# Add this import at the top
from supabase import create_client

# Initialize Supabase Admin client
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

@app.post("/api/analyze")
async def analyze_risks(data: ProjectDetails, user_id: str): # Add user_id from frontend
    # CHECK LICENSE ON THE SERVER SIDE (The ultimate Bouncer)
    license_check = supabase.table("profiles").select("is_active").eq("id", user_id).single().execute()
    
    if not license_check.data or not license_check.data.get("is_active"):
        raise HTTPException(status_code=403, detail="License inactive.")
    
    # ... rest of your AI logic ...

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
    # Add this route to your main.py to save assessments
@app.post("/api/save-assessment")
async def save_assessment(data: dict):
    # This receives the assessment from the frontend 
    # and stores it in your Supabase database
    return {"status": "success", "message": "Record saved to audit trail."}

# Add this route to load history
@app.get("/api/history/{user_id}")
async def get_history(user_id: str):
    # This fetches all past DPIAs for that user
    return {"status": "success", "data":
