from app.langgraph.tools.search_tool import search_web
from app.langgraph.state import GraphState
from app.langgraph.pydantics import WebSearchResponse

class WebSearchAgent:
    def __init__(self, web_search_tool=None):
        self.web_search_tool = web_search_tool or search_web

    def search(self, state: GraphState) -> WebSearchResponse:
        """Search the web for information"""
        query = state.rephrased_query or state.user_query
        return self.web_search_tool(query)
