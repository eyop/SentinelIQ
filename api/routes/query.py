from fastapi import APIRouter

from api.schemas import QueryRequest, QueryResponse
from rag.chain import answer_query

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
	"""Answer analyst queries using the RAG pipeline (or fallback)."""
	result = answer_query(request.question, k=request.k, severity_filter=request.severity_filter)
	return QueryResponse(answer=result["answer"], sources=result["sources"], retrieved_count=result["retrieved_count"])
