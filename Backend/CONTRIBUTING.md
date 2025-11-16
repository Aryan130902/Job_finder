
# Contributing Guidelines

Thank you for your interest in contributing to **EnableIt**!  
We follow professional, scalable engineering practices to ensure high-quality code.

---

## 🚀 Branching Model

- `main` → Protected branch (no direct commits)
- `dev` → Only merged via Pull Requests
- `feature/<feature_name>` → For feature development  
  Example: `feature/resume-parser`
- `bugfix/<bug_name>` → Patch or defect fixes  
- `docs/<doc_name>` → Documentation changes

---

## 📌 Pull Request Standards

### Every PR must:
- Target the `dev` branch
- Include a meaningful title + description
- Contain only **one feature or fix**
- Include unit tests for new code
- Pass:
  - linting (ruff)
  - typing checks (mypy)
  - test suite (pytest)
- Update documentation if applicable

---

## 🧪 Testing

Tests live inside `tests/`.  
Run tests:

```bash
pytest -q
