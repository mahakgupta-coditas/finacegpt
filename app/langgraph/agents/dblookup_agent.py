from app.langgraph.state import GraphState
from app.langgraph.pydantics import DatabaseLookupResponse
from app.services.retriever import search_pgvector

class DatabaseLookupAgent:
    def __init__(self, vector_db_tool=None):
        self.vector_db_tool = vector_db_tool or search_pgvector

    def _is_relevant_result(self, query: str, result: str) -> bool:
        if not result or len(result.strip()) < 20:
            return False

        query_lower = query.lower()
        result_lower = result.lower()

        generic_phrases = [
            'internal control over financial reporting',
            'see cognitive business operations',
            'computer programs designed to',
            'chatbots',
            'constant currency',
            'notes forming part of consolidated',
            'integrated annual report',
            'health & wellness award',
            'diversity in tech awards'
        ]

        generic_count = sum(1 for phrase in generic_phrases if phrase in result_lower)
        if generic_count > 1:
            return False

        financial_keywords = ['revenue', 'profit', 'earnings', 'sales', 'income', 'financial', 'report', 'annual']
        query_has_financial = any(keyword in query_lower for keyword in financial_keywords)

        if query_has_financial:
            financial_indicators = [
                '$', 'million', 'billion', 'revenue', 'profit', 'earnings',
                'sales', 'income', 'crore', '%', 'percent', 'assets', 'liabilities'
            ]
            result_has_financial = any(indicator in result_lower for indicator in financial_indicators)
            if not result_has_financial:
                return False

        food_keywords = ['eat', 'food', 'recipe', 'cooking', 'meal', 'healthy food']
        if any(keyword in query_lower for keyword in food_keywords):
            return False

        return True

    def search(self, state: GraphState) -> DatabaseLookupResponse:
        try:
            query = state.rephrased_query or state.user_query
            results = self.vector_db_tool(query)

            if results:
                for result in results:
                    content = result.get("content", "")
                    if self._is_relevant_result(query, content):
                        return DatabaseLookupResponse(
                            found=True,
                            answer=content,
                            source="internal_db"
                        )
                return DatabaseLookupResponse(found=False)
            else:
                return DatabaseLookupResponse(found=False)

        except Exception:
            return DatabaseLookupResponse(found=False)
