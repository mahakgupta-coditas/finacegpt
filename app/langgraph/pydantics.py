from pydantic import BaseModel, Field
from typing import Literal, Optional, List

class SupervisorResponse(BaseModel):
    decision: Literal["greeting", "intent"]
    message: Optional[str] = None

class IntentResponse(BaseModel):
    intent: Literal["financial_query", "comparison", "out_of_scope"]
    message: Optional[str] = None

class RephraseResponse(BaseModel):
    rephrased_query: str
    original_query: str

class DatabaseLookupResponse(BaseModel):
    found: bool
    answer: Optional[str] = None
    source: Optional[str] = None

class WebSearchResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    sources: List[str] = Field(default_factory=list)
    error: Optional[str] = None

class SummarizerResponse(BaseModel):
    summary: str
    sources: List[str] = Field(default_factory=list)

class OutOfScopeResponse(BaseModel):
    message: str
    suggestion: Optional[str] = None

class ComparisonResponse(BaseModel):
    comparison: str
    companies: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)