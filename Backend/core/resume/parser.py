from dataclasses import dataclass, field
from typing import Optional
import re


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


def parse_latex_resume(latex_path: str) -> Resume:
    with open(latex_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = LatexResumeParser(content)
    return parser.parse()
