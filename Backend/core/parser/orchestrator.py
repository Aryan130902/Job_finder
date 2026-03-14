"""
Centralized Resume Orchestrator.

This module provides a unified interface for all resume processing operations,
combining parsing, NER extraction, vector storage, and export capabilities.
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.parser.latex_parser import (
    LatexResumeParser,
    Resume,
    Skill as LatexSkill
)
from core.nlp.bert_ner import create_ner_extractor, BERTNERExtractor
from core.services.chromadb import get_chroma_service, ChromaDBService
from core.services.excel import get_excel_exporter, ExcelExporter


class ResumeOrchestrator:
    """
    Centralized orchestrator for all resume processing operations.
    
    Coordinates between LaTeX parsing, BERT NER extraction, ChromaDB storage,
    and Excel export to provide a unified resume processing interface.
    """
    
    def __init__(
        self,
        bert_model_path: Optional[str] = None,
        chroma_persist_dir: str = "./chroma_db"
    ):
        """
        Initialize the resume orchestrator.
        
        Args:
            bert_model_path: Optional path to BERT model
            chroma_persist_dir: Directory for ChromaDB persistence
        """
        self.ner_extractor = create_ner_extractor()
        self.chroma_service = get_chroma_service(chroma_persist_dir)
        self.excel_exporter = get_excel_exporter()
        
        self.device = self.ner_extractor.device
        self.bert_model = self.ner_extractor.bert_model
        self.bert_tokenizer = self.ner_extractor.tokenizer
    
    def parse_resume_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a resume file (LaTeX or text).
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Dictionary containing parsed resume data
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        return self.parse_resume_text(text)
    
    def parse_resume_text(self, text: str) -> Dict[str, Any]:
        """
        Parse resume from text content.
        
        Combines LaTeX parsing with BERT NER extraction to produce
        enriched resume data.
        
        Args:
            text: Raw resume text content
            
        Returns:
            Dictionary containing parsed and enriched resume data
        """
        extracted = self.ner_extractor.extract_from_text(text)
        
        latex_parser = LatexResumeParser(text)
        latex_resume = latex_parser.parse()
        
        resume_data = self._merge_extracted_data(extracted, latex_resume)
        
        resume_data["extracted_date"] = datetime.now().isoformat()
        
        return resume_data
    
    def _merge_extracted_data(
        self,
        extracted: Dict[str, List[str]],
        latex_resume: Resume
    ) -> Dict[str, Any]:
        """
        Merge NER extracted data with LaTeX parsed data.
        
        Args:
            extracted: Data extracted by BERT NER
            latex_resume: Data parsed from LaTeX
            
        Returns:
            Merged resume data dictionary
        """
        resume_data = {
            "name": extracted.get("name", [latex_resume.name])[0] if extracted.get("name") else latex_resume.name,
            "email": extracted.get("email", [latex_resume.email])[0] if extracted.get("email") else latex_resume.email,
            "phone": extracted.get("phone", [latex_resume.phone])[0] if extracted.get("phone") else latex_resume.phone,
            "linkedin": latex_resume.linkedin,
            "portfolio": latex_resume.portfolio,
            
            "education": extracted.get("education", []) or [e.degree for e in latex_resume.education],
            "skills": extracted.get("skills", []) or self._flatten_latex_skills(latex_resume.skills),
            "company_name": extracted.get("company", []) or [e.company for e in latex_resume.experience],
            "college_name": extracted.get("college", []),
            "designation": extracted.get("designation", []) or [e.role for e in latex_resume.experience],
            "experience": extracted.get("experience", []),
            "total_experience": self._calculate_total_experience(extracted.get("experience", [])),
            
            "raw_education": [e.__dict__ for e in latex_resume.education],
            "raw_experience": [e.__dict__ for e in latex_resume.experience],
            "raw_projects": [p.__dict__ for p in latex_resume.projects],
        }
        
        return resume_data
    
    def _flatten_latex_skills(self, skills: List[LatexSkill]) -> List[str]:
        """
        Flatten LaTeX skill categories into a single list.
        
        Args:
            skills: List of Skill objects from LaTeX parser
            
        Returns:
            Flat list of all skills
        """
        flat_skills = []
        for skill in skills:
            flat_skills.extend(skill.skills)
        return flat_skills
    
    def _calculate_total_experience(self, experience_list: List[str]) -> str:
        """
        Calculate total years of experience from experience list.
        
        Args:
            experience_list: List of experience descriptions
            
        Returns:
            String representation of total experience
        """
        if not experience_list:
            return ""
        
        total_years = 0
        for exp in experience_list:
            match = re.search(r'(\d+)', str(exp))
            if match:
                years = int(match.group(1))
                if years > total_years:
                    total_years = years
        
        return f"{total_years} years" if total_years > 0 else ""
    
    def save_to_chroma(self, resume_data: Dict[str, Any]) -> str:
        """
        Save resume to ChromaDB vector store.
        
        Args:
            resume_data: Resume data to store
            
        Returns:
            Generated resume ID
        """
        resume_id = self.chroma_service.add_resume(
            resume_data,
            self.bert_model,
            self.bert_tokenizer,
            self.device
        )
        return resume_id
    
    def export_to_excel(
        self,
        resume_data: Dict[str, Any],
        output_path: str
    ) -> bool:
        """
        Export resume to Excel file.
        
        Args:
            resume_data: Resume data to export
            output_path: Path to save the Excel file
            
        Returns:
            True if successful, False otherwise
        """
        return self.excel_exporter.export_single_resume(resume_data, output_path)
    
    def export_batch_to_excel(
        self,
        resumes: List[Dict[str, Any]],
        output_path: str
    ) -> bool:
        """
        Export multiple resumes to a single Excel file.
        
        Args:
            resumes: List of resume data dictionaries
            output_path: Path to save the Excel file
            
        Returns:
            True if successful, False otherwise
        """
        return self.excel_exporter.export_resumes(resumes, output_path)
    
    def search_resumes(
        self,
        query: str,
        search_type: str = "text"
    ) -> List[Dict]:
        """
        Search resumes using vector similarity.
        
        Args:
            query: Search query
            search_type: Type of search - "text", "skill", or "experience"
            top_k: Number of results to return
            
        Returns:
            List of matching resumes with metadata
        """
        if search_type == "skill":
            return self.chroma_service.search_by_skill(
                query, self.bert_model, self.bert_tokenizer, self.device
            )
        elif search_type == "experience":
            return self.chroma_service.search_by_experience(
                query, self.bert_model, self.bert_tokenizer, self.device
            )
        else:
            return self.chroma_service.search_by_text(
                query, self.bert_model, self.bert_tokenizer, self.device
            )
    
    def get_all_resumes(self) -> List[Dict]:
        """
        Get all stored resumes.
        
        Returns:
            List of all resume dictionaries
        """
        return self.chroma_service.get_all_resumes()
    
    def delete_resume(self, resume_id: str) -> bool:
        """
        Delete a resume from storage.
        
        Args:
            resume_id: ID of the resume to delete
            
        Returns:
            True if successful, False otherwise
        """
        return self.chroma_service.delete_resume(resume_id)
    
    def process_and_store(
        self,
        text: str,
        store_in_chroma: bool = True,
        export_to_excel: bool = False,
        excel_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete resume processing pipeline.
        
        Parses resume text, optionally stores in ChromaDB,
        and optionally exports to Excel.
        
        Args:
            text: Raw resume text
            store_in_chroma: Whether to store in vector database
            export_to_excel: Whether to export to Excel
            excel_path: Path for Excel export (required if export_to_excel is True)
            
        Returns:
            Complete resume data dictionary with storage/exort IDs
        """
        resume_data = self.parse_resume_text(text)
        
        if store_in_chroma:
            resume_id = self.save_to_chroma(resume_data)
            resume_data["chroma_id"] = resume_id
        
        if export_to_excel and excel_path:
            self.export_to_excel(resume_data, excel_path)
            resume_data["excel_path"] = excel_path
        
        return resume_data


_orchestrator = None


def get_orchestrator(
    bert_model_path: Optional[str] = None,
    chroma_persist_dir: str = "./chroma_db"
) -> ResumeOrchestrator:
    """
    Get or create a singleton ResumeOrchestrator instance.
    
    Args:
        bert_model_path: Optional path to BERT model
        chroma_persist_dir: Directory for ChromaDB persistence
        
    Returns:
        ResumeOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ResumeOrchestrator(bert_model_path, chroma_persist_dir)
    return _orchestrator


def create_orchestrator(
    bert_model_path: Optional[str] = None,
    chroma_persist_dir: str = "./chroma_db"
) -> ResumeOrchestrator:
    """
    Factory function to create a new ResumeOrchestrator instance.
    
    Use this when you need a fresh orchestrator instance.
    
    Args:
        bert_model_path: Optional path to BERT model
        chroma_persist_dir: Directory for ChromaDB persistence
        
    Returns:
        New ResumeOrchestrator instance
    """
    return ResumeOrchestrator(bert_model_path, chroma_persist_dir)
