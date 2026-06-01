from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from retail_intelligence.api.deps import get_db
from retail_intelligence.application.use_cases.ingest_event import IngestEventUseCase
from retail_intelligence.schemas.event import EventIngestItem, EventIngestResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/ingest", response_model=EventIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_event(
    payload: list[EventIngestItem] = Body(...),
    db: Session = Depends(get_db),
) -> EventIngestResponse:
    use_case = IngestEventUseCase(db=db)
    return use_case.execute(payload)
