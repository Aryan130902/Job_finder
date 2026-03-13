"""
Optimizer Module - ATS Resume Optimization.

This module provides functionality to optimize resumes for
Applicant Tracking Systems (ATS) based on job requirements.
"""

from core.optimizer.optimizer import (
    ATSResume,
    ResumeEditor,
    optimize_resume_for_job
)

__all__ = [
    "ATSResume",
    "ResumeEditor",
    "optimize_resume_for_job",
]
