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

# --- HELPER FUNCTION: This is required for your Word tables to work! ---
def add_formatted_text_to_word(doc, text):
    lines = text.split('\n')
    in_table = False
    table = None
    for line in lines:
        line = line.strip()
        if not line: continue
        if line.startswith('|'):
            parts = line.split('|')
            cells = [p.strip() for p in parts[1:-1]]
            if len(cells) > 0 and all(c.replace('-', '').strip() == '' for c in cells): continue
            if not in_table:
                table = doc.add_table(rows=1, cols=len(cells))
                table.style = 'Table Grid'
                for i, cell_text in enumerate(cells):
                    table.rows[0].cells[i].text = cell_text.replace('**', '')
                in_table = True
            else:
                row = table.add_row().cells
                for i, cell_text in enumerate(cells):
                    if i < len(row): row[i].text = cell_text.replace('**', '')
            continue
        else: in_table = False
        if line.startswith('## '): doc.add_heading(line[3:], level=2)
        elif line.startswith('# '): doc.add_heading(line[2:], level=1)
        else: doc.add_paragraph(line.replace('**', ''))

@app.post("/api/analyze")
async def analyze_risks(data: ProjectDetails):
    prompt = f"""Identify 3 privacy risks for: {data.project_name}. For each, provide Risk Description and Mitigation. Format as a clean list."""
    try:
        # USING THE RELIABLE ALIAS
        response = completion(model="claude-3-5-sonnet-20240620", messages=[{"role": "user", "content": prompt}])
        return {"status": "success", "risks": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-report")
async def generate_final_report(data: FinalReportRequest):
    prompt = f"""Write a DPIA for {data.project_name}. Use the risks: {data.identified_risks}. Include a Markdown table for Risks | Mitigation | Evidence."""
    try:
        response = completion(model="claude-3-5-sonnet-20240620", messages=[{"role": "user", "content": prompt}])
        ai_report = response.choices[0].message.content
        
        doc = Document()
        doc.add_heading('Data Protection Impact Assessment', 0)
        add_formatted_text_to_word(doc, ai_report)
        
        file_name = f"/tmp/{data.project_name.replace(' ', '_')}_DPIA.docx"
        doc.save(file_name)
        return FileResponse(path=file_name, filename="DPIA.docx", media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except Exception as e:
        return {"status": "error", "message": str(e)}
