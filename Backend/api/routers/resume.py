from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid

from core.resume.parser import (
    parse_latex_resume, 
    Resume, 
    EnhancedResumeParser,
    create_enhanced_parser
)
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


class ParseAndStoreRequest(BaseModel):
    store_in_chroma: Optional[bool] = True
    export_to_excel: Optional[bool] = False
    excel_path: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    search_type: Optional[str] = "text"
    top_k: Optional[int] = 10


_enhanced_parser = None

def get_enhanced_parser() -> EnhancedResumeParser:
    global _enhanced_parser
    if _enhanced_parser is None:
        _enhanced_parser = create_enhanced_parser()
    return _enhanced_parser


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


@router.post("/parse-ner")
async def parse_resume_with_ner(
    resume: UploadFile = File(...),
    store_in_chroma: bool = Query(True),
    export_to_excel: bool = Query(False),
    excel_path: Optional[str] = Query(None)
):
    try:
        content = await resume.read()
        text = content.decode('utf-8', errors='ignore')
        
        parser = get_enhanced_parser()
        
        resume_data = parser.process_and_store(
            text,
            store_in_chroma=store_in_chroma,
            export_to_excel=export_to_excel,
            excel_path=excel_path
        )
        
        return {
            "status": "success",
            "data": {
                "name": resume_data.get("name"),
                "email": resume_data.get("email"),
                "phone": resume_data.get("phone"),
                "education": resume_data.get("education"),
                "skills": resume_data.get("skills"),
                "company_name": resume_data.get("company_name"),
                "college_name": resume_data.get("college_name"),
                "designation": resume_data.get("designation"),
                "experience": resume_data.get("experience"),
                "total_experience": resume_data.get("total_experience"),
            },
            "chroma_id": resume_data.get("chroma_id"),
            "excel_path": resume_data.get("excel_path")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-text")
async def parse_resume_text(
    text: str,
    store_in_chroma: bool = Query(True),
    export_to_excel: bool = Query(False),
    excel_path: Optional[str] = Query(None)
):
    try:
        parser = get_enhanced_parser()
        
        resume_data = parser.process_and_store(
            text,
            store_in_chroma=store_in_chroma,
            export_to_excel=export_to_excel,
            excel_path=excel_path
        )
        
        return {
            "status": "success",
            "data": {
                "name": resume_data.get("name"),
                "email": resume_data.get("email"),
                "phone": resume_data.get("phone"),
                "education": resume_data.get("education"),
                "skills": resume_data.get("skills"),
                "company_name": resume_data.get("company_name"),
                "college_name": resume_data.get("college_name"),
                "designation": resume_data.get("designation"),
                "experience": resume_data.get("experience"),
                "total_experience": resume_data.get("total_experience"),
            },
            "chroma_id": resume_data.get("chroma_id"),
            "excel_path": resume_data.get("excel_path")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_resumes(
    query: str = Query(...),
    search_type: str = Query("text"),
    top_k: int = Query(10)
):
    try:
        parser = get_enhanced_parser()
        
        results = parser.search_resumes(query, search_type, top_k)
        
        return {
            "status": "success",
            "query": query,
            "search_type": search_type,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_resumes():
    try:
        parser = get_enhanced_parser()
        resumes = parser.get_all_resumes()
        
        return {
            "status": "success",
            "count": len(resumes),
            "resumes": resumes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{resume_id}")
async def delete_resume(resume_id: str):
    try:
        parser = get_enhanced_parser()
        success = parser.delete_resume(resume_id)
        
        if success:
            return {"status": "success", "message": f"Resume {resume_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail="Resume not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-excel")
async def export_resumes_to_excel(
    resume_ids: List[str] = None,
    output_path: str = Query("resumes_export.xlsx")
):
    try:
        parser = get_enhanced_parser()
        
        if resume_ids:
            resumes = []
            for rid in resume_ids:
                all_resumes = parser.get_all_resumes()
                for r in all_resumes:
                    if r.get("id") == rid:
                        resumes.append(r.get("metadata", {}))
                        break
        else:
            all_resumes = parser.get_all_resumes()
            resumes = [r.get("metadata", {}) for r in all_resumes]
        
        if not resumes:
            raise HTTPException(status_code=404, detail="No resumes found")
        
        success = parser.export_batch_to_excel(resumes, output_path)
        
        if success:
            return {
                "status": "success",
                "message": f"Exported {len(resumes)} resumes to {output_path}",
                "output_path": output_path
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to export to Excel")
    except HTTPException:
        raise
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
