import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from litellm import completion
from supabase import create_client

# 1. Initialize FastAPI
app = FastAPI(title="DPIA Enterprise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Crash-Proof Environment Variables
SUPA_URL = os.environ.get("SUPABASE_URL")
SUPA_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not SUPA_URL or not SUPA_KEY:
    raise ValueError("CRITICAL ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY is missing!")

# Initialize Supabase and Anthropic/Google clients
supabase = create_client(SUPA_URL, SUPA_KEY)
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# 3. Data Models
class ProjectDetails(BaseModel):
    project_name: str
    project_desc: str
    data_subjects: str
    data_collected: str
    retention: str
    third_parties: str
    initial_risk: str
    user_id: str

# 4. API Routes
@app.get("/")
def home():
    return {"message": "✅ DPIA Engine is live and clean!"}

@app.post("/api/analyze")
async def analyze_risks(data: ProjectDetails):
    # License Check
    license_check = supabase.table("profiles").select("is_active").eq("id", data.user_id).single().execute()
    if not license_check.data or not license_check.data.get("is_active"):
        raise HTTPException(status_code=403, detail="License inactive.")
    
    # AI Logic
    prompt = f"Identify 3 privacy risks for: {data.project_name}. Description: {data.project_desc}. Provide Description and Mitigation."
    try:
        response = completion(
            model="gemini/gemini-1.5-flash", 
            messages=[{"role": "user", "content": prompt}]
        )
        return {"status": "success", "risks": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/save-assessment")
async def save_assessment(data: dict):
    try:
        supabase.table("assessments").insert(data).execute()
        return {"status": "success", "message": "Record saved."}
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
