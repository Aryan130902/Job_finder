from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import resume

app = FastAPI(
    title="Resume ATS Optimizer API",
    description="API for parsing and optimizing resumes for ATS",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router)


@app.get("/")
def root():
    return {"message": "Resume ATS Optimizer API", "status": "running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}