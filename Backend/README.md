# Resume ATS Optimizer

An AI-powered job application assistant designed to help candidates generate high-scoring ATS-optimized resumes tailored to specific job descriptions.

## Overview

This system analyzes a user's base resume (in LaTeX format), finds relevant jobs, and enhances the resume to better match job descriptions so that it performs well in Applicant Tracking Systems (ATS).

## Features

- **LaTeX Resume Parsing**: Parse and extract structured information from LaTeX resumes
- **BERT NER Extraction**: Extract entities (name, email, skills, experience) using BERT-based NER
- **Vector Search**: Store and search resumes using ChromaDB vector embeddings
- **ATS Optimization**: Optimize resume content for specific job descriptions
- **Document Generation**: Generate optimized resumes in TXT or DOCX format
- **Excel Export**: Export resume data to Excel for easy viewing

## Tech Stack

- **Python 3.10+**: Primary programming language
- **FastAPI**: REST API framework
- **BERT (bert-base-uncased)**: Named Entity Recognition model
- **ChromaDB**: Vector database for semantic search
- **OpenPyXL**: Excel export functionality

## Project Structure

```
Backend/
├── api/                    # FastAPI application and routers
│   ├── routers/
│   │   └── resume.py       # Resume-related endpoints
│   └── __init__.py
├── core/                   # Core business logic
│   ├── parser/             # Resume parsing
│   │   ├── latex_parser.py    # LaTeX parsing
│   │   └── orchestrator.py    # Central resume processing
│   ├── nlp/               # NLP components
│   │   └── bert_ner.py        # BERT NER extractor
│   ├── services/           # External services
│   │   ├── chromadb.py        # Vector storage
│   │   └── excel.py           # Excel export
│   ├── optimizer/         # Resume optimization
│   │   ├── optimizer.py        # ATS optimization logic
│   │   └── generator.py        # Document generation
│   └── jobs/              # Job analysis
│       └── analyzer.py         # Job description analyzer
├── models/                 # Pydantic models (future use)
├── tests/                 # Test suite
├── docs/                  # Documentation
├── main.py               # Application entry point
└── requirements.txt       # Python dependencies
```

## Installation

1. **Clone the repository**
   ```bash
   cd Backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download BERT model** (if not already cached)
   The first run will automatically download the BERT model to:
   `C:\Users\<username>\.cache\huggingface\hub\`

## Running the Application

### Development Server

```bash
cd Backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Health Check: http://localhost:8000/health

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Resume Parsing

- `POST /api/v1/resume/parse` - Parse LaTeX resume file
- `POST /api/v1/resume/parse-ner` - Parse with NER extraction and optional storage
- `POST /api/v1/resume/parse-text` - Parse raw text with NER

### Resume Management

- `GET /api/v1/resume/all` - Get all stored resumes
- `GET /api/v1/resume/search` - Search resumes by query
- `DELETE /api/v1/resume/{resume_id}` - Delete a resume
- `POST /api/v1/resume/export-excel` - Export resumes to Excel

### Resume Optimization

- `POST /api/v1/resume/optimize` - Optimize resume for job description
- `POST /api/v1/resume/optimize-text` - Optimize default resume

## Usage Examples

### Parse a Resume

```python
import requests

with open("resume.tex", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/resume/parse-ner",
        files={"resume": f},
        data={"store_in_chroma": True}
    )
print(response.json())
```

### Optimize for Job Description

```python
import requests

job_description = """
Software Engineer
Requirements:
- 3+ years experience with Python
- Experience with React
- AWS knowledge
"""

response = requests.post(
    "http://localhost:8000/api/v1/resume/optimize-text",
    json={
        "job_description": job_description,
        "company_name": "TechCorp"
    }
)
print(response.json())
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Linting
ruff check .

# Type checking
mypy .

# Formatting
black .
isort .
```

## License

MIT License

## Contributing

See CONTRIBUTING.md for guidelines.
