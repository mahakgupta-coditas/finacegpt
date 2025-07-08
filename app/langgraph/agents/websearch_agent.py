from app.langgraph.tools.search_tool import search_web
from app.langgraph.state import GraphState
from app.langgraph.pydantics import WebSearchResponse

class WebSearchAgent:
    def __init__(self, web_search_tool=None):
        self.web_search_tool = web_search_tool or search_web
    
    def search(self, state: GraphState) -> WebSearchResponse:
        """Search the web for information"""
        try:
            query = state.rephrased_query or state.user_query
            result = self.web_search_tool(query)
            
            # Handle different return formats from the search tool
            if isinstance(result, dict):
                return WebSearchResponse(
                    success=result.get('success', False),
                    content=result.get('content', ''),
                    sources=result.get('sources', []),
                    error=result.get('error', None)
                )
            elif isinstance(result, WebSearchResponse):
                return result
            else:
                # If it's just a string result
                return WebSearchResponse(
                    success=True,
                    content=str(result),
                    sources=[]
                )
                
        except Exception as e:
            return WebSearchResponse(
                success=False,
                content=None,
                sources=[],
                error=f"Web search failed: {str(e)}"
            )