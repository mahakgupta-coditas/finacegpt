from pydantic import BaseModel
from typing import List

class ComparisonRequest(BaseModel):
    query: str
    session_id: str
    companies: List[str] = []  

class ComparisonResponse(BaseModel):
    comparison: str
    companies: List[str]
    sources: List[str]