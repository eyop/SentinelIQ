from fastapi import APIRouter

from api.schemas import IngestRequest
from scripts.ingest_now import run_ingestion

router = APIRouter(tags=["ingest"])


@router.post("/ingest")
async def ingest(request: IngestRequest) -> dict[str, int]:
    return run_ingestion(lookback_days=request.lookback_days)
