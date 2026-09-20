from typing import TypedDict, List

class AgentState(TypedDict):
    question:str
    documents:List
    context:str
    answer:str
    citations:List
