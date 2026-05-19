import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from litellm import completion
from supabase import create_client
from docx import Document

app = FastAPI(title="DPIA Enterprise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Clients
os.environ["GOOGLE_API_KEY"] = os.environ.get("GOOGLE_API_KEY")
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_KEY"))

class ProjectDetails(BaseModel):
    project_name: str
    project_desc: str
    data_subjects: str
    data_collected: str
    retention: str
    third_parties: str
    initial_risk: str
    user_id: str

@app.post("/api/analyze")
async def analyze_risks(data: ProjectDetails):
    prompt = f"Identify 3 privacy risks for: {data.project_name}. Provide Description and Mitigation."
    try:
        # Using Gemini Flash - Global and Fast
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

@app.get("/")
def home():
    return {"message": "✅ API Active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
