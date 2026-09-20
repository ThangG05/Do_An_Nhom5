from pydantic import BaseModel


class InternalLLMTestResponse(BaseModel):
    status: str
    provider: str
    model: str
    answer: str
    cited_context_ids: list[str]
