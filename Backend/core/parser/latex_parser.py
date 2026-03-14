"""
Resume Parsing Module.

This module provides LaTeX resume parsing functionality using dataclasses
for internal representation.
"""

import re
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class Education:
    """Represents educational background."""
    institution: str
    degree: str
    cgpa: Optional[str] = None
    year: str = ""


@dataclass
class Experience:
    """Represents work experience."""
    company: str
    location: str
    role: str
    duration: str
    bullet_points: list = field(default_factory=list)


@dataclass
class Project:
    """Represents a project."""
    name: str
    link: Optional[str] = None
    tech_stack: Optional[str] = None
    year: str = ""
    bullet_points: list = field(default_factory=list)


@dataclass
class Skill:
    """Represents a skill category."""
    category: str
    skills: list = field(default_factory=list)


@dataclass
class Position:
    """Represents a position of responsibility."""
    title: str
    organization: str
    duration: str
    description: str = ""


@dataclass
class Achievement:
    """Represents an achievement."""
    title: str
    description: str
    year: str = ""


@dataclass
class Resume:
    """Represents a parsed resume."""
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


def _clean(text: str) -> str:
    """Strip LaTeX formatting commands and extra whitespace from a string."""
    # Remove \textbf{...}, \textit{...}, \footnotesize{...}, etc.
    text = re.sub(r'\\(?:textbf|textit|emph|footnotesize|small|large|Large|href\{[^}]*\})\{([^}]*)\}', r'\1', text)
    # Remove standalone commands like \textbf, \small, etc.
    text = re.sub(r'\\[a-zA-Z]+\*?', '', text)
    # Remove leftover braces
    text = re.sub(r'[{}]', '', text)
    # Collapse whitespace
    return re.sub(r'\s+', ' ', text).strip()


def _extract_section(content: str, section_name: str) -> Optional[str]:
    """
    Extract the raw content of a named section.
    Sections are delimited by \\section{...} headers.
    """
    pattern = rf'\\section\{{[^}}]*{re.escape(section_name)}[^}}]*\}}(.*?)(?=\\section|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    return match.group(1) if match else None


def _extract_item_bullets(block: str) -> List[str]:
    """
    Extract all \\item {...} bullet points from a block of LaTeX.
    Handles items that may span multiple lines inside braces.
    """
    bullets = []
    # Match \item followed by optional space and a brace-enclosed block
    for m in re.finditer(r'\\item\s*\{((?:[^{}]|\{[^{}]*\})*)\}', block, re.DOTALL):
        bullets.append(_clean(m.group(1)))
    # Also match \item without braces (plain text until next \item or end)
    # Used for positions/achievements inline descriptions
    return bullets


class LatexResumeParser:
    """
    Parser for LaTeX formatted resumes.

    Extracts structured information from LaTeX resume files including
    personal info, education, experience, projects, skills, and achievements.
    """

    def __init__(self, latex_content: str):
        self.content = latex_content

    def parse(self) -> Resume:
        resume = Resume(
            name=self._extract_name(),
            phone=self._extract_phone(),
            email=self._extract_email(),
            linkedin=self._extract_linkedin(),
            portfolio=self._extract_portfolio(),
        )
        resume.education = self._extract_education()
        resume.experience = self._extract_experience()
        resume.projects = self._extract_projects()
        resume.skills = self._extract_skills()
        resume.positions = self._extract_positions()
        resume.achievements = self._extract_achievements()
        return resume

    # ------------------------------------------------------------------
    # Header fields
    # ------------------------------------------------------------------

    def _extract_name(self) -> str:
        r"""Matches: \textbf{\Large Aryan Tiwari}"""
        match = re.search(r'\\textbf\{\\Large\s+([^}]+)\}', self.content)
        return match.group(1).strip() if match else ""

    def _extract_phone(self) -> str:
        """Matches the phone number after the faPhone icon."""
        match = re.search(r'\\faPhone[\\~ ]+([+\d\s\-]+)', self.content)
        return match.group(1).strip() if match else ""

    def _extract_email(self) -> str:
        r"""Matches: \href{mailto:email}{...}"""
        match = re.search(r'\\href\{mailto:([^}]+)\}', self.content)
        return match.group(1).strip() if match else ""

    def _extract_linkedin(self) -> Optional[str]:
        r"""Matches: \href{https://linkedin.com/...}{LinkedIn Profile}"""
        match = re.search(r'\\href\{([^}]+)\}\{LinkedIn Profile\}', self.content)
        return match.group(1).strip() if match else None

    def _extract_portfolio(self) -> Optional[str]:
        r"""Matches: \href{https://...}{Portfolio Website}"""
        match = re.search(r'\\href\{([^}]+)\}\{Portfolio Website\}', self.content)
        return match.group(1).strip() if match else None

    # ------------------------------------------------------------------
    # Education
    # ------------------------------------------------------------------

    def _extract_education(self) -> List[Education]:
        """
        LaTeX pattern:
            \\resumeSubheading
            {Institution}{CGPA : 8.2}
            {Degree}{Year}
        """
        section = _extract_section(self.content, 'Education')
        if not section:
            return []

        education = []
        # resumeSubheading takes 4 args: {arg1}{arg2}{arg3}{arg4}
        # In the template: arg1=institution, arg2=CGPA/grade, arg3=degree, arg4=year
        pattern = (
            r'\\resumeSubheading\s*'
            r'\{([^}]+)\}\s*'   # institution
            r'\{([^}]+)\}\s*'   # CGPA line  (e.g. "CGPA : 8.2")
            r'\{([^}]+)\}\s*'   # degree
            r'\{([^}]+)\}'      # year
        )
        for m in re.finditer(pattern, section, re.DOTALL):
            institution, cgpa_raw, degree, year = (g.strip() for g in m.groups())
            # Extract numeric CGPA if present
            cgpa_match = re.search(r'[\d.]+', cgpa_raw)
            cgpa = cgpa_match.group(0) if cgpa_match else cgpa_raw
            education.append(Education(
                institution=_clean(institution),
                degree=_clean(degree),
                cgpa=cgpa,
                year=_clean(year),
            ))
        return education

    # ------------------------------------------------------------------
    # Experience
    # ------------------------------------------------------------------

    def _extract_experience(self) -> List[Experience]:
        """
        LaTeX pattern:
            \\resumeSubheading{Company}{Location}{Role}{Duration}
            \\resumeItemListStart
              \\item {bullet ...}
            \\resumeItemListEnd
        """
        section = _extract_section(self.content, 'Experience')
        if not section:
            return []

        experiences = []
        # Split on each \resumeSubheading to get per-entry blocks
        entry_pattern = (
            r'\\resumeSubheading\s*'
            r'\{([^}]+)\}\s*'   # company
            r'\{([^}]+)\}\s*'   # location
            r'\{([^}]+)\}\s*'   # role
            r'\{([^}]+)\}'      # duration
        )
        # Find all subheading positions
        matches = list(re.finditer(entry_pattern, section))
        for i, m in enumerate(matches):
            company, location, role, duration = (g.strip() for g in m.groups())
            # The bullet block is everything between this match's end and the next match's start
            block_start = m.end()
            block_end = matches[i + 1].start() if i + 1 < len(matches) else len(section)
            block = section[block_start:block_end]
            bullets = _extract_item_bullets(block)
            experiences.append(Experience(
                company=_clean(company),
                location=_clean(location),
                role=_clean(role),
                duration=_clean(duration),
                bullet_points=bullets,
            ))
        return experiences

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def _extract_projects(self) -> List[Project]:
        """
        LaTeX pattern:
            \\resumeProject{Name}{Link or Tech Stack}{Year}{optional 4th}
            \\resumeItemListStart
              \\item {bullet}
            \\resumeItemListEnd
        """
        section = _extract_section(self.content, 'Projects')
        if not section:
            return []

        projects = []
        entry_pattern = (
            r'\\resumeProject\s*'
            r'\{([^}]+)\}\s*'          # name
            r'\{((?:[^{}]|\{[^}]*\})*)\}\s*'  # link or tech (may contain \href{...}{...})
            r'\{([^}]*)\}'             # year
            r'(?:\s*\{([^}]*)\})?'     # optional 4th arg
        )
        matches = list(re.finditer(entry_pattern, section))
        for i, m in enumerate(matches):
            name = m.group(1).strip()
            second_arg = m.group(2).strip()
            year = m.group(3).strip()

            # Determine if second arg is a hyperlink or a tech stack description
            href_match = re.search(r'\\href\{([^}]+)\}', second_arg)
            if href_match:
                link = href_match.group(1).strip()
                tech_stack = None
            else:
                link = None
                # Strip "Tech Stack : " prefix if present
                tech_stack = re.sub(r'^Tech Stack\s*:\s*', '', _clean(second_arg)).strip()

            block_start = m.end()
            block_end = matches[i + 1].start() if i + 1 < len(matches) else len(section)
            block = section[block_start:block_end]
            bullets = _extract_item_bullets(block)

            projects.append(Project(
                name=_clean(name),
                link=link,
                tech_stack=tech_stack,
                year=_clean(year),
                bullet_points=bullets,
            ))
        return projects

    # ------------------------------------------------------------------
    # Skills
    # ------------------------------------------------------------------

    def _extract_skills(self) -> List[Skill]:
        """
        LaTeX pattern:
            \\textbf{Category}: skill1, skill2, ...
        """
        section = _extract_section(self.content, 'Skills')
        if not section:
            return []

        skills = []
        # Matches \textbf{Category}: comma-separated skills (rest of the line)
        pattern = r'\\textbf\{([^}]+)\}\s*:\s*([^\n\\]+)'
        for m in re.finditer(pattern, section):
            category = m.group(1).strip()
            raw_skills = m.group(2).strip()
            # Split on commas, clean each entry
            skill_list = [s.strip() for s in raw_skills.split(',') if s.strip()]
            skills.append(Skill(category=category, skills=skill_list))
        return skills

    # ------------------------------------------------------------------
    # Positions of Responsibility
    # ------------------------------------------------------------------

    def _extract_positions(self) -> List[Position]:
        """
        LaTeX pattern:
            \\resumePOR{Title, }{Organization}{Duration}
            Inline description text on next line(s).
        """
        section = _extract_section(self.content, 'Positions')
        if not section:
            return []

        positions = []
        entry_pattern = (
            r'\\resumePOR\s*'
            r'\{([^}]*)\}\s*'   # title (may end with ", ")
            r'\{([^}]+)\}\s*'   # organization
            r'\{([^}]+)\}'      # duration
        )
        matches = list(re.finditer(entry_pattern, section))
        for i, m in enumerate(matches):
            title = m.group(1).strip().rstrip(',').strip()
            organization = m.group(2).strip()
            duration = m.group(3).strip()

            # Description is the text between this entry and the next \resumePOR
            block_start = m.end()
            block_end = matches[i + 1].start() if i + 1 < len(matches) else len(section)
            raw_desc = section[block_start:block_end]
            # Stop at any LaTeX command block / section end markers
            raw_desc = re.split(r'\\resumeSubHeadingListEnd|\\vspace|\\section', raw_desc)[0]
            description = _clean(raw_desc)

            positions.append(Position(
                title=_clean(title),
                organization=_clean(organization),
                duration=_clean(duration),
                description=description,
            ))
        return positions

    # ------------------------------------------------------------------
    # Achievements
    # ------------------------------------------------------------------

    def _extract_achievements(self) -> List[Achievement]:
        """
        LaTeX pattern:
            \\resumePOR{optional prefix}{Achievement description}{Year}

        The resume uses arg1 as optional prefix (e.g., award name) and
        arg2 as the main description text.
        """
        section = _extract_section(self.content, 'Achievements')
        if not section:
            return []

        achievements = []
        entry_pattern = (
            r'\\resumePOR\s*'
            r'\{([^}]*)\}\s*'                        # arg1: title/prefix (may be empty)
            r'\{((?:[^{}]|\{[^}]*\})*)\}\s*'         # arg2: description (handles \textbf{...} etc.)
            r'\{([^}]+)\}'                           # arg3: year
        )
        for m in re.finditer(entry_pattern, section):
            prefix = _clean(m.group(1))
            description = _clean(m.group(2))
            year = m.group(3).strip()

            # When arg1 is empty the full description lives in arg2
            if prefix:
                title = prefix
            else:
                title = description
                description = ""

            achievements.append(Achievement(
                title=title,
                description=description,
                year=year,
            ))
        return achievements


def parse_latex_resume(file_path: str) -> Resume:
    """
    Utility function to parse a LaTeX resume file.

    Args:
        file_path: Path to the LaTeX resume file

    Returns:
        Parsed Resume object

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    parser = LatexResumeParser(content)
    return parser.parse()
