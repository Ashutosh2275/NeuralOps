from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.api.deps import get_session
from sentinelops.api.schemas.nlp import NLPQueryRequest, NLPQueryResponse
from sentinelops.config import get_settings
from sentinelops.services.nlp_service import NLPInfrastructureService

router = APIRouter()


@router.post("/query", response_model=NLPQueryResponse)
async def nlp_query(
    body: NLPQueryRequest,
    session: AsyncSession = Depends(get_session),
) -> NLPQueryResponse:
    settings = get_settings()
    if not settings.feature_nlp_assistant:
        return NLPQueryResponse(question=body.question, answer="NLP assistant is disabled.", sources=[])
    service = NLPInfrastructureService(session)
    result = await service.query(body.question, body.namespace)
    return NLPQueryResponse(
        question=result["question"],
        answer=result["answer"],
        sources=result.get("sources", []),
    )
