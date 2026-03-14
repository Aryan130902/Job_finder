"""
Resume API Router.

This module provides FastAPI endpoints for resume parsing,
optimization, and management.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid

from core.parser.latex_parser import parse_latex_resume
from core.parser.orchestrator import get_orchestrator, create_orchestrator
from core.optimizer.optimizer import optimize_resume_for_job
from core.optimizer.generator import generate_resume_document


router = APIRouter(prefix="/resume", tags=["resume"])


class JobDescriptionRequest(BaseModel):
    """Request model for job description optimization."""
    job_description: str
    company_name: Optional[str] = "Default"


class OptimizeRequest(BaseModel):
    """Request model for resume optimization."""
    resume_path: str
    job_description: str
    company_name: Optional[str] = "Default"
    output_format: Optional[str] = "txt"


class ParseAndStoreRequest(BaseModel):
    """Request model for parsing and storing resume."""
    store_in_chroma: Optional[bool] = True
    export_to_excel: Optional[bool] = False
    excel_path: Optional[str] = None


class SearchRequest(BaseModel):
    """Request model for resume search."""
    query: str
    search_type: Optional[str] = "text"
    top_k: Optional[int] = 10


_enhanced_parser = None


def get_enhanced_parser():
    """Get or create singleton enhanced parser."""
    global _enhanced_parser
    if _enhanced_parser is None:
        _enhanced_parser = create_orchestrator()
    return _enhanced_parser


@router.post("/parse")
async def parse_resume(resume: UploadFile = File(...)):
    """
    Parse a LaTeX resume file.
    
    Upload a LaTeX resume file to extract structured information.
    """
    try:
        content = await resume.read()
        
        temp_path = f"temp_{uuid.uuid4()}.tex"
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        parsed_resume = parse_latex_resume(temp_path)
        
        os.remove(temp_path)
        
        return parsed_resume
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-ner")
async def parse_resume_with_ner(
    resume: UploadFile = File(...),
    store_in_chroma: bool = Query(True),
    export_to_excel: bool = Query(False),
    excel_path: Optional[str] = Query(None)
):
    """
    Parse a resume with NER and optionally store in ChromaDB.
    
    Upload a resume (text or LaTeX) to extract entities using BERT NER,
    optionally store in vector database, and optionally export to Excel.
    """
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
    """
    Parse resume from text content.
    
    Provide raw resume text to extract entities using BERT NER,
    optionally store in vector database, and optionally export to Excel.
    """
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
    query: str = Query(..., description="Search query"),
    search_type: str = Query("text", description="Type of search: text, skill, or experience"),
    top_k: int = Query(10, description="Number of results to return")
):
    """
    Search resumes using vector similarity.
    
    Search stored resumes by semantic similarity using BERT embeddings.
    """
    try:
        parser = get_enhanced_parser()
        
        results = parser.search_resumes(query, search_type)
        results = results[:top_k]
        
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
    """
    Get all stored resumes.
    
    Retrieve all resumes stored in the vector database.
    """
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
    """
    Delete a resume from storage.
    
    Remove a resume and its embeddings from the vector database.
    """
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
    resume_ids: Optional[List[str]] = Query(None, description="List of resume IDs to export"),
    output_path: str = Query("resumes_export.xlsx", description="Output file path")
):
    """
    Export resumes to Excel.
    
    Export selected or all resumes to an Excel spreadsheet.
    """
    try:
        parser = get_enhanced_parser()
        
        if resume_ids and len(resume_ids) > 0:
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
    """
    Optimize a resume for a job description.
    
    Parse a LaTeX resume and optimize it for ATS compatibility
    based on the provided job description.
    """
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
    """
    Optimize the default resume for a job description.
    
    Uses the default main.tex resume and optimizes it for
    the provided job description.
    """
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
