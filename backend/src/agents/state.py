from typing import TypedDict

class AgentState(TypedDict, total=False):
    query: str
    context: str
    answer: str
    sources: list
