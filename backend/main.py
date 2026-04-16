from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from services.repo_analyzer import RepositoryAnalyzer


class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl


app = FastAPI(title="ArchiteXt v2", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = RepositoryAnalyzer()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze_repository(payload: AnalyzeRequest) -> dict:
    repo_url = str(payload.repo_url)
    if "github.com" not in repo_url:
        raise HTTPException(status_code=400, detail="Only GitHub repository URLs are supported")

    try:
        return analyzer.analyze_from_url(repo_url)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
