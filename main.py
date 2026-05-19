import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import anthropic
from supabase import create_client

app = FastAPI(title="DPIA Enterprise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Clients
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_KEY"))

class ProjectDetails(BaseModel):
    project_name: str
    project_desc: str
    data_subjects: str
    data_collected: str
    retention: str
    third_parties: str
    initial_risk: str
    user_id: str  # Added so we can check license

@app.get("/")
def home():
    return {"message": "✅ DPIA Engine is live and clean!"}

@app.post("/api/analyze")
async def analyze_risks(data: ProjectDetails):
    # 1. License Check
    license_check = supabase.table("profiles").select("is_active").eq("id", data.user_id).single().execute()
    if not license_check.data or not license_check.data.get("is_active"):
        raise HTTPException(status_code=403, detail="License inactive.")
    
    # 2. AI Logic
    prompt = f"Identify privacy risks for: {data.project_name}. Description: {data.project_desc}. Provide Description and Mitigation."
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"status": "success", "risks": response.content[0].text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/save-assessment")
async def save_assessment(data: dict):
    try:
        supabase.table("assessments").insert(data).execute()
        return {"status": "success", "message": "Record saved to audit trail."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/history/{user_id}")
async def get_history(user_id: str):
    try:
        response = supabase.table("assessments").select("*").eq("user_id", user_id).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}
        if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
