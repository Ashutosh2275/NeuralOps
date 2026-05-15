from pydantic import BaseModel, Field


class NLPQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    namespace: str | None = None


class NLPQueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]
