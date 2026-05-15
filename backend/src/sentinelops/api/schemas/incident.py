from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class IncidentSummary(BaseModel):
    id: UUID
    title: str
    status: str
    severity: str
    root_service: str | None
    confidence_score: float | None
    started_at: datetime

    model_config = {"from_attributes": True}


class IncidentResponse(IncidentSummary):
    root_cause: str | None
    affected_services: list[str] = []
    cascade_chain: list[dict] = []
    timeline: list[dict] = []
