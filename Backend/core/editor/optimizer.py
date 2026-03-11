from typing import List, Dict, Optional
from dataclasses import dataclass, field
from core.resume.parser import Resume, Experience, Project, Skill
from core.jobs.analyzer import JobRequirements


@dataclass
class ATSResume:
    name: str
    phone: str
    email: str
    linkedin: Optional[str] = None
    summary: str = ""
    experience: List[Dict] = field(default_factory=list)
    projects: List[Dict] = field(default_factory=list)
    skills: Dict[str, List[str]] = field(default_factory=dict)
    education: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        self.experience = self.experience or []
        self.projects = self.projects or []
        self.skills = self.skills or {}
        self.education = self.education or []


class ResumeEditor:
    def __init__(self, resume: Resume, requirements: JobRequirements):
        self.resume = resume
        self.requirements = requirements
        self.job_keywords = set(k.lower() for k in requirements.keywords)
    
    def optimize_for_ats(self) -> ATSResume:
        ats_resume = ATSResume(
            name=self.resume.name,
            phone=self.resume.phone,
            email=self.resume.email,
            linkedin=self.resume.linkedin,
        )
        
        ats_resume.summary = self._generate_summary()
        ats_resume.experience = self._optimize_experience()
        ats_resume.projects = self._optimize_projects()
        ats_resume.skills = self._optimize_skills()
        ats_resume.education = self._optimize_education()
        
        return ats_resume
    
    def _generate_summary(self) -> str:
        role = self.requirements.title or "Software Engineer"
        
        primary_skills = self.requirements.required_skills[:3]
        skills_str = ", ".join(primary_skills) if primary_skills else "software development"
        
        years = ""
        if self.requirements.experience_years:
            years = f" with {self.requirements.experience_years}+ years of experience"
        
        summary = f"{role} with expertise in {skills_str}{years}. "
        summary += "Proven track record of delivering scalable solutions."
        
        return summary
    
    def _optimize_experience(self) -> List[Dict]:
        optimized = []
        
        for exp in self.resume.experience:
            exp_dict = {
                "company": exp.company,
                "location": exp.location,
                "role": exp.role,
                "duration": exp.duration,
                "bullet_points": []
            }
            
            for bullet in exp.bullet_points:
                optimized_bullet = self._ats_optimize_bullet(bullet)
                if optimized_bullet:
                    exp_dict["bullet_points"].append(optimized_bullet)
            
            if not exp_dict["bullet_points"]:
                for bullet in exp.bullet_points:
                    exp_dict["bullet_points"].append(bullet)
            
            optimized.append(exp_dict)
        
        return optimized
    
    def _ats_optimize_bullet(self, bullet: str) -> Optional[str]:
        bullet_lower = bullet.lower()
        
        if any(kw in bullet_lower for kw in self.job_keywords):
            return bullet
        
        for keyword in self.requirements.required_skills:
            keyword_lower = keyword.lower()
            
            skill_mappings = {
                'python': ['python', 'py'],
                'java': ['java'],
                'javascript': ['javascript', 'js'],
                'react': ['react', 'reactjs'],
                'node': ['node', 'nodejs'],
                '.net': ['.net', 'dotnet', 'asp.net'],
                'aws': ['aws', 'amazon web services'],
                'azure': ['azure'],
                'docker': ['docker'],
                'kubernetes': ['kubernetes', 'k8s'],
                'sql': ['sql', 'database', 'mysql', 'postgresql'],
                'machine learning': ['ml', 'machine learning', 'ai'],
            }
            
            if keyword_lower in skill_mappings:
                for variant in skill_mappings[keyword_lower]:
                    if variant in bullet_lower:
                        return bullet
        
        return None
    
    def _optimize_projects(self) -> List[Dict]:
        optimized = []
        
        for proj in self.resume.projects:
            proj_dict = {
                "name": proj.name,
                "link": proj.link,
                "tech_stack": proj.tech_stack or "",
                "year": proj.year,
                "bullet_points": []
            }
            
            for bullet in proj.bullet_points:
                optimized_bullet = self._ats_optimize_bullet(bullet)
                if optimized_bullet:
                    proj_dict["bullet_points"].append(optimized_bullet)
            
            if not proj_dict["bullet_points"]:
                proj_dict["bullet_points"] = proj.bullet_points[:2]
            
            optimized.append(proj_dict)
        
        return optimized
    
    def _optimize_skills(self) -> Dict[str, List[str]]:
        optimized_skills = {}
        
        all_resume_skills = []
        for skill in self.resume.skills:
            all_resume_skills.extend(skill.skills)
        
        required_set = set(s.lower() for s in self.requirements.required_skills)
        preferred_set = set(s.lower() for s in self.requirements.preferred_skills)
        
        matched_required = []
        matched_preferred = []
        other_skills = []
        
        for skill in all_resume_skills:
            skill_lower = skill.lower()
            
            if skill_lower in required_set:
                matched_required.append(skill)
            elif skill_lower in preferred_set:
                matched_preferred.append(skill)
            else:
                other_skills.append(skill)
        
        if matched_required:
            optimized_skills["Technical Skills"] = matched_required
        if matched_preferred:
            optimized_skills["Preferred Skills"] = matched_preferred
        if other_skills:
            optimized_skills["Additional Skills"] = other_skills[:10]
        
        for req_skill in self.requirements.required_skills:
            if req_skill.lower() not in [s.lower() for s in optimized_skills.get("Technical Skills", [])]:
                if "Technical Skills" not in optimized_skills:
                    optimized_skills["Technical Skills"] = []
                if len(optimized_skills["Technical Skills"]) < 15:
                    optimized_skills["Technical Skills"].append(req_skill)
        
        return optimized_skills
    
    def _optimize_education(self) -> List[Dict]:
        optimized = []
        
        for edu in self.resume.education:
            edu_dict = {
                "institution": edu.institution,
                "degree": edu.degree,
                "cgpa": edu.cgpa,
                "year": edu.year
            }
            optimized.append(edu_dict)
        
        return optimized


def optimize_resume_for_job(resume: Resume, job_description: str) -> ATSResume:
    from core.jobs.analyzer import analyze_job_description
    
    requirements = analyze_job_description(job_description)
    editor = ResumeEditor(resume, requirements)
    return editor.optimize_for_ats()
