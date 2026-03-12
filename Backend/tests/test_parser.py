import sys
import os
import tempfile

# ensure top-level `Backend` package is importable when tests run
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.resume.parser import parse_latex_resume


LATEX_SAMPLE = r"""
\textbf{\Large John Doe}
\faPhone 123-456-7890
\href{mailto:jdoe@example.com}{jdoe@example.com}
\section{Experience}
\resumeSubheading{Company}{Location}{Role}{2020-2022}
\item{Worked on something}
"""


def test_parse_latex_resume_basic(tmp_path):
    temp_file = tmp_path / "sample.tex"
    temp_file.write_text(LATEX_SAMPLE)

    resume = parse_latex_resume(str(temp_file))
    assert resume.name == "John Doe"
    assert "123-456-7890" in resume.phone
    assert resume.email == "jdoe@example.com"
    assert resume.experience and resume.experience[0].company == "Company"
