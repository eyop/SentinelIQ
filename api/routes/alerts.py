from fastapi import APIRouter

from api.schemas import AlertResponse

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts() -> list[AlertResponse]:
	"""Return an empty alert list until SIEM correlation is implemented."""
	return []
