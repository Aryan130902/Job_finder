import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from core.resume.bert_ner_extractor import create_ner_extractor, BERTNERExtractor
from core.resume.chroma_service import ChromaDBService, get_chroma_service
from core.resume.excel_exporter import ExcelExporter, get_excel_exporter


@dataclass
class Education:
    institution: str
    degree: str
    cgpa: Optional[str] = None
    year: str = ""


@dataclass
class Experience:
    company: str
    location: str
    role: str
    duration: str
    bullet_points: list = field(default_factory=list)


@dataclass
class Project:
    name: str
    link: Optional[str] = None
    tech_stack: Optional[str] = None
    year: str = ""
    bullet_points: list = field(default_factory=list)


@dataclass
class Skill:
    category: str
    skills: list = field(default_factory=list)


@dataclass
class Position:
    title: str
    organization: str
    duration: str
    description: str = ""


@dataclass
class Achievement:
    title: str
    description: str
    year: str = ""


@dataclass
class Resume:
    name: str
    phone: str
    email: str
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    education: list = field(default_factory=list)
    experience: list = field(default_factory=list)
    projects: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    positions: list = field(default_factory=list)
    achievements: list = field(default_factory=list)


class LatexResumeParser:
    def __init__(self, latex_content: str):
        self.content = latex_content
    
    def parse(self) -> Resume:
        resume = Resume(
            name=self._extract_name(),
            phone=self._extract_phone(),
            email=self._extract_email(),
            linkedin=self._extract_linkedin(),
            portfolio=self._extract_portfolio()
        )
        
        resume.education = self._extract_education()
        resume.experience = self._extract_experience()
        resume.projects = self._extract_projects()
        resume.skills = self._extract_skills()
        resume.positions = self._extract_positions()
        resume.achievements = self._extract_achievements()
        
        return resume
    
    def _extract_name(self) -> str:
        match = re.search(r'\\textbf\{\\Large\s*([^}]+)\}', self.content)
        return match.group(1).strip() if match else ""
    
    def _extract_phone(self) -> str:
        match = re.search(r'\\faPhone[^}]*([\d\-\s\+]+)', self.content)
        return match.group(1).strip() if match else ""
    
    def _extract_email(self) -> str:
        match = re.search(r'\\href\{mailto:([^}]+)\}', self.content)
        return match.group(1).strip() if match else ""
    
    def _extract_linkedin(self) -> Optional[str]:
        match = re.search(r'LinkedIn Profile\s*\\href\{([^}]+)\}', self.content)
        return match.group(1).strip() if match else None
    
    def _extract_portfolio(self) -> Optional[str]:
        match = re.search(r'Portfolio Website\s*\\href\{([^}]+)\}', self.content)
        return match.group(1).strip() if match else None
    
    def _extract_education(self) -> list:
        education = []
        pattern = r'\\resumeSubheading\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}'
        matches = re.findall(pattern, self.content)
        
        for match in matches:
            if 'CGPA' in match[1] or 'CGPA' in match[2]:
                education.append(Education(
                    institution=match[0],
                    cgpa=match[1],
                    degree=match[2],
                    year=match[3]
                ))
        return education
    
    def _extract_experience(self) -> list:
        experience = []
        exp_section = re.search(r'\\section\{Experience\}(.*?)(?=\\section|\Z)', self.content, re.DOTALL)
        if not exp_section:
            return experience
        
        exp_content = exp_section.group(1)
        entries = re.findall(
            r'\\resumeSubheading\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}',
            exp_content
        )
        
        for entry in entries:
            bullets = re.findall(
                r'\\item\s*\{([^}]+)\}',
                exp_content
            )
            
            company = entry[0]
            role = entry[2]
            location = entry[1]
            duration = entry[3]
            
            exp_bullets = []
            for bullet in bullets:
                if company in bullet or role in bullet:
                    exp_bullets.append(bullet.strip())
            
            experience.append(Experience(
                company=company,
                location=location,
                role=role,
                duration=duration,
                bullet_points=exp_bullets
            ))
        
        return experience
    
    def _extract_projects(self) -> list:
        projects = []
        proj_section = re.search(r'\\section\{Projects\}(.*?)(?=\\section|\Z)', self.content, re.DOTALL)
        if not proj_section:
            return projects
        
        proj_content = proj_section.group(1)
        entries = re.findall(
            r'\\resumeProject\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}(?:\{([^}]+)\})?',
            proj_content
        )
        
        for entry in entries:
            bullets = re.findall(r'\\item\s*\{([^}]+)\}', proj_content)
            projects.append(Project(
                name=entry[0],
                link=entry[1] if 'http' in entry[1] else None,
                tech_stack=entry[1] if 'http' not in entry[1] else None,
                year=entry[2],
                bullet_points=bullets
            ))
        
        return projects
    
    def _extract_skills(self) -> list:
        skills = []
        skill_section = re.search(
            r'\\section\{Technical.*?Skills\}(.*?)(?=\\section|\Z)',
            self.content,
            re.DOTALL
        )
        if not skill_section:
            return skills
        
        skill_content = skill_section.group(1)
        
        category_matches = re.findall(
            r'\\textbf\{([^}]+)\}:\s*([^\n]+)',
            skill_content
        )
        
        for category, skill_list in category_matches:
            skills.append(Skill(
                category=category.strip(),
                skills=[s.strip() for s in skill_list.split(',')]
            ))
        
        return skills
    
    def _extract_positions(self) -> list:
        positions = []
        pos_section = re.search(
            r'\\section\{Positions.*?\}(.*?)(?=\\section|\Z)',
            self.content,
            re.DOTALL
        )
        if not pos_section:
            return positions
        
        pos_content = pos_section.group(1)
        entries = re.findall(
            r'\\resumePOR\{([^}]*)\}\{([^}]+)\}\{([^}]+)\}',
            pos_content
        )
        
        for entry in entries:
            positions.append(Position(
                title=entry[0].strip(),
                organization=entry[1],
                duration=entry[2]
            ))
        
        return positions
    
    def _extract_achievements(self) -> list:
        achievements = []
        ach_section = re.search(
            r'\\section\{Achievements\}(.*?)(?=\\section|\Z)',
            self.content,
            re.DOTALL
        )
        if not ach_section:
            return achievements
        
        ach_content = ach_section.group(1)
        entries = re.findall(
            r'\\resumePOR\{([^}]*)\}\{([^}]+)\}\{([^}]+)\}',
            ach_content
        )
        
        for entry in entries:
            achievements.append(Achievement(
                title=entry[1].strip(),
                description=entry[0].strip(),
                year=entry[2]
            ))
        
        return achievements


class EnhancedResumeParser:
    def __init__(
        self,
        bert_model_path: Optional[str] = None,
        chroma_persist_dir: str = "./chroma_db"
    ):
        self.ner_extractor = create_ner_extractor()
        self.chroma_service = get_chroma_service(chroma_persist_dir)
        self.excel_exporter = get_excel_exporter()
        
        self.device = self.ner_extractor.device
        self.bert_model = self.ner_extractor.bert_model
        self.bert_tokenizer = self.ner_extractor.tokenizer
    
    def parse_resume_file(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        return self.parse_resume_text(text)
    
    def parse_resume_text(self, text: str) -> Dict[str, Any]:
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
    
    def _flatten_latex_skills(self, skills: List[Skill]) -> List[str]:
        flat_skills = []
        for skill in skills:
            flat_skills.extend(skill.skills)
        return flat_skills
    
    def _calculate_total_experience(self, experience_list: List[str]) -> str:
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
    
    def save_to_chroma(
        self,
        resume_data: Dict[str, Any]
    ) -> str:
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
        return self.excel_exporter.export_single_resume(resume_data, output_path)
    
    def export_batch_to_excel(
        self,
        resumes: List[Dict[str, Any]],
        output_path: str
    ) -> bool:
        return self.excel_exporter.export_resumes(resumes, output_path)
    
    def search_resumes(
        self,
        query: str,
        search_type: str = "text"
    ) -> List[Dict]:
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
        return self.chroma_service.get_all_resumes()
    
    def delete_resume(self, resume_id: str) -> bool:
        return self.chroma_service.delete_resume(resume_id)
    
    def process_and_store(
        self,
        text: str,
        store_in_chroma: bool = True,
        export_to_excel: bool = False,
        excel_path: Optional[str] = None
    ) -> Dict[str, Any]:
        resume_data = self.parse_resume_text(text)
        
        if store_in_chroma:
            resume_id = self.save_to_chroma(resume_data)
            resume_data["chroma_id"] = resume_id
        
        if export_to_excel and excel_path:
            self.export_to_excel(resume_data, excel_path)
            resume_data["excel_path"] = excel_path
        
        return resume_data


def parse_latex_resume(file_path: str) -> Resume:
    """Utility to read a LaTeX resume file and return a parsed Resume object.

    This function is used by the API routers and re‑exported from
    ``core.resume`` and ``core.latex_parser``. It simply loads the file
    content and delegates to :class:`LatexResumeParser`.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    parser = LatexResumeParser(content)
    return parser.parse()


def create_enhanced_parser(
    bert_model_path: Optional[str] = None,
    chroma_persist_dir: str = "./chroma_db"
) -> EnhancedResumeParser:
    return EnhancedResumeParser(bert_model_path, chroma_persist_dir)
