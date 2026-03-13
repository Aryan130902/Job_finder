# Contributing Guidelines

Thank you for your interest in contributing to the Resume ATS Optimizer project!

---

## Branching Model

- `main` - Protected branch (no direct commits)
- `dev` - Development branch, merged via Pull Requests
- `feature/<feature_name>` - For feature development  
  Example: `feature/resume-parser`
- `bugfix/<bug_name>` - Patch or defect fixes
- `docs/<doc_name>` - Documentation changes

---

## Pull Request Standards

### Every PR must:

1. **Target the `dev` branch** (not main)
2. **Include a meaningful title + description**
3. **Contain only one feature or fix**
4. **Include unit tests for new code**
5. **Pass all checks:**
   - Linting: `ruff check .`
   - Type checking: `mypy .`
   - Test suite: `pytest tests/`
6. **Update documentation** if applicable

---

## Development Setup

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/job_finder.git
   cd job_finder/Backend
   ```

3. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Code Style

- Follow **PEP 8** guidelines
- Use **type hints** for all function signatures
- Add **docstrings** to all public functions and classes
- Keep lines under **100 characters** when possible
- Use **meaningful variable names**

### Example Function

```python
def process_resume(
    text: str,
    store: bool = True
) -> dict[str, Any]:
    """
    Process a resume text and optionally store in database.
    
    Args:
        text: Raw resume text content
        store: Whether to store in vector database
        
    Returns:
        Dictionary containing parsed resume data
        
    Raises:
        ValueError: If text is empty
    """
    if not text.strip():
        raise ValueError("Resume text cannot be empty")
    
    # Processing logic here...
    return {"name": "John Doe", "skills": ["Python"]}
```

---

## Testing

Tests are located in the `tests/` directory.

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_parser.py -v

# Run with coverage
pytest tests/ --cov=core --cov-report=html
```

### Writing Tests

```python
import pytest
from core.parser.latex_parser import parse_latex_resume


def test_parse_latex_resume_basic(tmp_path):
    """Test basic LaTeX resume parsing."""
    temp_file = tmp_path / "sample.tex"
    temp_file.write_text(r"""
    \textbf{\Large John Doe}
    \faPhone 123-456-7890
    \hrefmailto{jdoe@example.com}
    """)
    
    resume = parse_latex_resume(str(temp_file))
    assert resume.name == "John Doe"
    assert resume.phone == "123-456-7890"
```

---

## Commit Messages

Use clear, descriptive commit messages:

- `feat: add resume parsing from text content`
- `fix: resolve issue with skill extraction`
- `docs: update API documentation`
- `refactor: improve parser error handling`

---

## Questions?

- Open an issue for bug reports or feature requests
- Use discussions for questions
- Check existing issues before creating new ones

---

## Code of Conduct

Be respectful and inclusive. Follow the project's code of conduct.
