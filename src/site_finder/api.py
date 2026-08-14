"""FastAPI app for candidate-site screening."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .engine import find_candidate_sites
from .models import BuildingEnvelope, Parcel, ParcelAssessment

app = FastAPI(title="Adelaide Site Finder", version="0.1.0")


class CandidateRequest(BaseModel):
    """Request body for in-memory parcel screening."""

    envelope: BuildingEnvelope
    parcels: list[Parcel]
    include_failures: bool = False


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/candidates", response_model=list[ParcelAssessment])
def candidates(request: CandidateRequest) -> list[ParcelAssessment]:
    results = find_candidate_sites(request.parcels, request.envelope)
    if request.include_failures:
        return results
    return [result for result in results if result.status != "fail"]
