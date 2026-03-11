from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import uuid

from core.resume.parser import parse_latex_resume, Resume
from core.editor.optimizer import optimize_resume_for_job, ATSResume
from core.editor.generator import generate_resume_document


router = APIRouter(prefix="/resume", tags=["resume"])


class JobDescriptionRequest(BaseModel):
    job_description: str
    company_name: Optional[str] = "Default"


class OptimizeRequest(BaseModel):
    resume_path: str
    job_description: str
    company_name: Optional[str] = "Default"
    output_format: Optional[str] = "txt"


@router.post("/parse")
async def parse_resume(resume: UploadFile = File(...)):
    try:
        content = await resume.read()
        
        temp_path = f"temp_{uuid.uuid4()}.tex"
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        parsed_resume = parse_latex_resume(temp_path)
        
        os.remove(temp_path)
        
        return {
            "name": parsed_resume.name,
            "email": parsed_resume.email,
            "phone": parsed_resume.phone,
            "education": [
                {"institution": e.institution, "degree": e.degree, "cgpa": e.cgpa, "year": e.year}
                for e in parsed_resume.education
            ],
            "experience": [
                {"company": e.company, "role": e.role, "location": e.location, "duration": e.duration}
                for e in parsed_resume.experience
            ],
            "skills": [
                {"category": s.category, "skills": s.skills}
                for s in parsed_resume.skills
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize_resume(request: OptimizeRequest):
    try:
        if not os.path.exists(request.resume_path):
            raise HTTPException(status_code=404, detail="Resume file not found")
        
        parsed_resume = parse_latex_resume(request.resume_path)
        
        ats_resume = optimize_resume_for_job(parsed_resume, request.job_description)
        
        output_dir = f"output/{request.company_name}"
        os.makedirs(output_dir, exist_ok=True)
        
        output_format = request.output_format or "txt"
        output_path = f"{output_dir}/resume_{output_format}"
        
        success = generate_resume_document(ats_resume, output_path, output_format)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to generate resume")
        
        return {
            "message": "Resume optimized successfully",
            "output_path": output_path,
            "ats_resume": {
                "name": ats_resume.name,
                "summary": ats_resume.summary,
                "skills": ats_resume.skills
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-text")
async def optimize_resume_text(request: JobDescriptionRequest):
    try:
        latex_path = "main.tex"
        
        if not os.path.exists(latex_path):
            raise HTTPException(status_code=404, detail="Default resume (main.tex) not found")
        
        parsed_resume = parse_latex_resume(latex_path)
        
        ats_resume = optimize_resume_for_job(parsed_resume, request.job_description)
        
        output_dir = f"output/{request.company_name}"
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = f"{output_dir}/resume.txt"
        generate_resume_document(ats_resume, output_path, "txt")
        
        return {
            "message": "Resume optimized successfully",
            "output_path": output_path,
            "ats_resume": {
                "name": ats_resume.name,
                "summary": ats_resume.summary,
                "experience_count": len(ats_resume.experience),
                "skills": ats_resume.skills
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))