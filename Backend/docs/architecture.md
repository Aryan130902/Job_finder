# Architecture Documentation

## System Overview

The Resume ATS Optimizer is an AI-powered system designed to help candidates create ATS-optimized resumes. It uses modern NLP techniques and vector search to parse, analyze, and optimize resumes for specific job descriptions.

## Architecture Principles

1. **Clean Architecture** - Separation of concerns with distinct layers
2. **Single Responsibility** - Each module has a focused purpose
3. **Dependency Injection** - Services are injected rather than hard-coded
4. **Singleton Pattern** - For expensive resources (BERT models, ChromaDB)

## Layer Architecture

```
┌─────────────────────────────────────────────┐
│           API Layer (FastAPI)                │
│  - Endpoints                                 │
│  - Request/Response Models                   │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Core Business Logic Layer           │
│  ┌─────────┐ ┌─────────┐ ┌─────────────┐   │
│  │ Parser  │ │   NLP   │ │  Optimizer  │   │
│  └─────────┘ └─────────┘ └─────────────┘   │
│  ┌─────────┐ ┌─────────┐                   │
│  │  Jobs   │ │Services │                   │
│  └─────────┘ └─────────┘                   │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│        External Services Layer             │
│  - ChromaDB (Vector Storage)               │
│  - File System                             │
│  - BERT Model (HuggingFace)                │
└─────────────────────────────────────────────┘
```

## Module Descriptions

### API Layer (`api/`)

**Purpose**: FastAPI application and HTTP endpoints

**Components**:
- `main.py` - Application entry point, CORS setup
- `routers/resume.py` - All resume-related endpoints

**Key Responsibilities**:
- HTTP request handling
- Input validation with Pydantic
- Error handling and responses

---

### Core Layer (`core/`)

#### Parser Module (`core/parser/`)

**Purpose**: Resume parsing and orchestration

**Components**:
- `latex_parser.py` - Parses LaTeX resume format
- `orchestrator.py` - Central coordinator for all resume processing

**Key Classes**:
```python
LatexResumeParser    # Parses LaTeX resumes into dataclasses
ResumeOrchestrator   # Coordinates parsing, NER, storage, export
```

#### NLP Module (`core/nlp/`)

**Purpose**: Natural Language Processing for entity extraction

**Components**:
- `bert_ner.py` - BERT-based Named Entity Recognition

**Key Classes**:
```python
BERTNERExtractor     # Extracts entities using BERT model
```

#### Services Module (`core/services/`)

**Purpose**: External service integrations

**Components**:
- `chromadb.py` - Vector database for semantic search
- `excel.py` - Excel export functionality

**Key Classes**:
```python
ChromaDBService      # Vector storage and search
ExcelExporter       # Excel file generation
```

#### Optimizer Module (`core/optimizer/`)

**Purpose**: ATS resume optimization

**Components**:
- `optimizer.py` - ATS optimization logic
- `generator.py` - Document generation

**Key Classes**:
```python
ResumeEditor        # Optimizes resume for ATS
DocumentGenerator   # Generates output documents
```

#### Jobs Module (`core/jobs/`)

**Purpose**: Job description analysis

**Components**:
- `analyzer.py` - Extracts requirements from job descriptions

**Key Classes**:
```python
JobDescriptionAnalyzer  # Parses job postings
```

---

## Data Flow

### Resume Parsing Flow

```
Upload File → Parse LaTeX → Extract NER → Merge Data → Return JSON
```

1. User uploads LaTeX resume
2. `LatexResumeParser` extracts structured data
3. `BERTNERExtractor` enriches with NER
4. `ResumeOrchestrator` merges results
5. Returns parsed JSON

### Resume Storage Flow

```
Parse Resume → Generate Embeddings → Store in ChromaDB
```

1. Resume text is parsed
2. BERT generates vector embeddings
3. ChromaDB stores embeddings with metadata
4. Resume ID returned for future reference

### Resume Search Flow

```
Query → Generate Embedding → Semantic Search → Return Results
```

1. User provides search query
2. BERT generates query embedding
3. ChromaDB performs similarity search
4. Top-k results returned with metadata

### Resume Optimization Flow

```
Parse Resume → Analyze Job Description → Optimize Content → Generate Document
```

1. LaTeX resume is parsed
2. Job description analyzed for keywords
3. Resume content optimized for ATS
4. Document generated (TXT/DOCX)

---

## Dependency Graph

```
main.py
    └── api/routers/resume.py
            ├── core.parser.latex_parser
            ├── core.parser.orchestrator
            ├── core.optimizer.optimizer
            └── core.optimizer.generator
                    ├── core.parser.latex_parser.Resume
                    └── core.jobs.analyzer
                            └── core.parser.latex_parser
```

---

## Design Patterns

### Singleton Pattern

Used for expensive resources:
- `BERTNERExtractor` - One model instance
- `ChromaDBService` - One DB connection
- `ResumeOrchestrator` - One instance with loaded models

### Factory Pattern

```python
create_ner_extractor()    # Creates NER extractor
create_orchestrator()     # Creates new orchestrator
get_chroma_service()     # Gets or creates singleton
```

### Repository Pattern

`ChromaDBService` acts as a repository for resume embeddings with:
- `add_resume()`
- `get_resume_by_id()`
- `get_all_resumes()`
- `delete_resume()`
- `search_by_text()`

---

## Error Handling

- **API Level**: HTTPException with meaningful messages
- **Service Level**: Try-catch with boolean returns
- **Parser Level**: Exception propagation with context

---

## Performance Considerations

1. **Model Loading**: BERT models are loaded once and cached
2. **Database**: ChromaDB uses persistent storage
3. **Lazy Loading**: Services are initialized on first use
4. **Vector Batching**: Embeddings computed efficiently

---

## Future Improvements

1. Add caching layer (Redis)
2. Implement async processing
3. Add more document formats (PDF)
4. Implement user authentication
5. Add resume versioning
6. Implement webhooks for async processing
