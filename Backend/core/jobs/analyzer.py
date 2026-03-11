from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re


@dataclass
class JobRequirements:
    title: str = ""
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    experience_years: Optional[int] = None
    responsibilities: List[str] = field(default_factory=list)
    qualifications: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


COMMON_SKILL_PATTERNS = [
    r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|Ruby|Go|Rust|Swift|Kotlin|Scala|PHP|Perl|R)\b',
    r'\b(React|Angular|Vue|Node\.js|Express|Django|Flask|Spring|Rails|Laravel)\b',
    r'\b(AWS|Azure|GCP|Docker|Kubernetes|Terraform|Ansible|Jenkins|CircleCI)\b',
    r'\b(SQL|NoSQL|MongoDB|PostgreSQL|MySQL|Redis|Elasticsearch|Cassandra)\b',
    r'\b(Machine Learning|Deep Learning|NLP|Computer Vision|TensorFlow|PyTorch|Keras)\b',
    r'\b(Agile|Scrum|JIRA|Git|DevOps|CI/CD|MLOps)\b',
    r'\b(REST API|GraphQL|Microservices|gRPC|WebSocket)\b',
    r'\b(Data Engineering|Data Science|Analytics|ETL|Apache Spark|Hadoop)\b',
    r'\b(.NET|ASP\.NET|C\+\+|C#|VB\.NET|ADO\.NET|Entity Framework)\b',
    r'\b(HTML|CSS|Tailwind|Bootstrap|SASS|LESS)\b',
]


class JobDescriptionAnalyzer:
    def __init__(self, job_description: str):
        self.job_description = job_description.lower()
        self.original_text = job_description
    
    def analyze(self) -> JobRequirements:
        requirements = JobRequirements()
        
        requirements.title = self._extract_title()
        requirements.required_skills = self._extract_required_skills()
        requirements.preferred_skills = self._extract_preferred_skills()
        requirements.experience_years = self._extract_experience()
        requirements.responsibilities = self._extract_responsibilities()
        requirements.qualifications = self._extract_qualifications()
        requirements.keywords = self._extract_all_keywords()
        
        return requirements
    
    def _extract_title(self) -> str:
        title_patterns = [
            r'(?:job title|position|role)[\s:]+([^\n]+)',
            r'^([A-Z][a-zA-Z\s]+(?:Engineer|Developer|Manager|Analyst|Architect|Specialist))',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, self.original_text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        lines = self.original_text.split('\n')
        for line in lines[:5]:
            if any(kw in line.lower() for kw in ['engineer', 'developer', 'manager', 'analyst']):
                return line.strip()
        
        return ""
    
    def _extract_skills_by_pattern(self) -> List[str]:
        skills = []
        
        for pattern in COMMON_SKILL_PATTERNS:
            matches = re.findall(pattern, self.job_description, re.IGNORECASE)
            skills.extend([s.strip() for s in matches])
        
        skills = list(set([s.title() for s in skills]))
        
        tech_terms = ['AWS', 'Azure', 'GCP', 'SQL', 'NoSQL', 'API', 'CI/CD', 'ETL', 
                      'ML', 'AI', 'NLP', 'REST', 'GraphQL', 'SaaS', 'PaaS', 'IaaS',
                      '.NET', 'C#', 'C++', 'React', 'Vue', 'Angular', 'Node', 'Docker',
                      'Kubernetes', 'K8s', 'Redis', 'MongoDB', 'PostgreSQL', 'MySQL']
        
        for term in tech_terms:
            if term.lower() in self.job_description and term not in skills:
                skills.append(term)
        
        return skills
    
    def _extract_required_skills(self) -> List[str]:
        all_skills = self._extract_skills_by_pattern()
        
        required_keywords = ['required', 'must have', 'minimum', 'essential', 'required skills']
        preferred_keywords = ['preferred', 'nice to have', 'bonus', 'plus', 'desired']
        
        required_section = ""
        preferred_section = ""
        
        for kw in required_keywords:
            pattern = rf'{kw}[:\s]+(.*?)(?={" ".join(preferred_keywords)}|$)'
            match = re.search(pattern, self.job_description, re.IGNORECASE | re.DOTALL)
            if match:
                required_section += match.group(1)
        
        if not required_section:
            return all_skills[:15]
        
        required = []
        for skill in all_skills:
            if skill.lower() in required_section:
                required.append(skill)
        
        return required if required else all_skills[:10]
    
    def _extract_preferred_skills(self) -> List[str]:
        all_skills = self._extract_skills_by_pattern()
        required = self._extract_required_skills()
        
        return [s for s in all_skills if s not in required]
    
    def _extract_experience(self) -> Optional[int]:
        patterns = [
            r'(\d+)\+?\s+years?\s+(?:of\s+)?experience',
            r'minimum\s+(\d+)\s+years?',
            r'(\d+)-(\d+)\s+years?',
            r'experience\s+(?:of\s+)?(\d+)\+?\s+years?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.job_description)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_responsibilities(self) -> List[str]:
        responsibilities = []
        
        patterns = [
            r'responsibilities[:\s]+(.*?)(?=(?:qualifications|requirements|skills)|$)',
            r'duties[:\s]+(.*?)(?=(?:qualifications|requirements|skills)|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.job_description, re.IGNORECASE | re.DOTALL)
            if match:
                items = re.findall(r'[-•*]\s*([^\n]+)', match.group(1))
                responsibilities.extend(items)
        
        return responsibilities[:10]
    
    def _extract_qualifications(self) -> List[str]:
        qualifications = []
        
        patterns = [
            r'qualifications[:\s]+(.*?)(?=(?:responsibilities|skills|benefits)|$)',
            r'(?:education|requirements)[:\s]+(.*?)(?=(?:responsibilities|skills|benefits)|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.job_description, re.IGNORECASE | re.DOTALL)
            if match:
                items = re.findall(r'[-•*]\s*([^\n]+)', match.group(1))
                qualifications.extend(items)
        
        return qualifications[:10]
    
    def _extract_all_keywords(self) -> List[str]:
        keywords = set()
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', self.job_description)
        
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 
                      'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him',
                      'his', 'how', 'its', 'may', 'now', 'old', 'see', 'than', 'that',
                      'this', 'to', 'was', 'will', 'with', 'have', 'from', 'they', 
                      'what', 'were', 'when', 'more', 'some', 'into', 'year', 'your',
                      'been', 'would', 'their', 'there', 'also', 'experience', 'work',
                      'team', 'including', 'required', 'preferred', 'knowledge'}
        
        for word in words:
            if word.lower() not in stop_words:
                keywords.add(word.title())
        
        skills = self._extract_skills_by_pattern()
        keywords.update(skills)
        
        return list(keywords)[:50]


def analyze_job_description(job_description: str) -> JobRequirements:
    analyzer = JobDescriptionAnalyzer(job_description)
    return analyzer.analyze()
