from langgraph.graph import StateGraph, END
from app.langgraph.state import GraphState
from app.langgraph.agents.supervisor_agent import SupervisorAgent
from app.langgraph.agents.intent_agent import IntentAgent
from app.langgraph.agents.rephraser_agent import RephraserAgent
from app.langgraph.agents.dblookup_agent import DatabaseLookupAgent
from app.langgraph.agents.websearch_agent import WebSearchAgent
from app.langgraph.agents.summarizer_agent import SummarizerAgent
from app.langgraph.agents.memory_agent import MemoryAgent
from app.services.llm_call import LLMService

class FinanceGPTGraph:
    def __init__(self, vector_db_tool=None, web_search_tool=None, db=None):
        self.llm_service = LLMService()
        self.supervisor = SupervisorAgent(self.llm_service)
        self.intent_agent = IntentAgent(self.llm_service)
        self.rephraser = RephraserAgent(self.llm_service)
        self.db_lookup = DatabaseLookupAgent(vector_db_tool)
        self.web_search = WebSearchAgent(web_search_tool)
        self.summarizer = SummarizerAgent(self.llm_service)
        self.memory = MemoryAgent(db)

    def create_graph(self):
        workflow = StateGraph(GraphState)

        workflow.add_node("supervisor", self.supervisor_node)
        workflow.add_node("greeting", self.greeting_node)
        workflow.add_node("intent", self.intent_node)
        workflow.add_node("rephraser", self.rephraser_node)
        workflow.add_node("db_lookup", self.db_lookup_node)
        workflow.add_node("web_search", self.web_search_node)
        workflow.add_node("summarizer", self.summarizer_node)
        workflow.add_node("memory", self.memory_node)
        workflow.add_node("out_of_scope", self.out_of_scope_node)

        workflow.set_entry_point("supervisor")

        workflow.add_conditional_edges("supervisor", self.supervisor_router, {
            "greeting": "greeting",
            "intent": "intent",
            "rephrase": "rephraser"
        })

        workflow.add_conditional_edges("intent", self.intent_router, {
            "financial_query": "rephraser",
            "greeting": "greeting",
            "out_of_scope": "out_of_scope"
        })

        workflow.add_edge("greeting", END)
        workflow.add_edge("out_of_scope", END)
        workflow.add_edge("rephraser", "db_lookup")

        workflow.add_conditional_edges("db_lookup", self.db_lookup_router, {
            "found": "summarizer",
            "not_found": "web_search"
        })

        workflow.add_edge("web_search", "summarizer")
        workflow.add_edge("summarizer", "memory")
        workflow.add_edge("memory", END)

        return workflow.compile()

    def supervisor_node(self, state: GraphState) -> GraphState:
        try:
            result = self.supervisor.analyze(state)
            state.route_decision = result.decision
        except Exception:
            state.route_decision = "intent"
        return state

    def greeting_node(self, state: GraphState) -> GraphState:
        state.final_answer = (
            "Hello! I'm FinanceGPT, your financial assistant. "
            "I can provide financial data, company reports, investment insights, and more. "
            "How can I assist you today?"
        )
        return state

    def intent_node(self, state: GraphState) -> GraphState:
        try:
            result = self.intent_agent.classify(state)
            state.route_decision = result.intent
            if hasattr(result, 'confidence'):
                state.intent_confidence = result.confidence
        except Exception:
            state.route_decision = "out_of_scope"
        return state

    def rephraser_node(self, state: GraphState) -> GraphState:
        try:
            result = self.rephraser.rephrase(state)
            state.rephrased_query = result.rephrased_query
        except Exception:
            state.rephrased_query = state.user_query
        return state

    def db_lookup_node(self, state: GraphState) -> GraphState:
        try:
            result = self.db_lookup.search(state)
            if result.found and result.answer:
                state.db_result = result.answer
                state.route_decision = "found"
                if result.source:
                    state.sources.append(result.source)
            else:
                state.route_decision = "not_found"
        except Exception:
            state.route_decision = "not_found"

        if not state.route_decision:
            state.route_decision = "not_found"
        return state

    def web_search_node(self, state: GraphState) -> GraphState:
        try:
            if not self.web_search or not hasattr(self.web_search, 'search'):
                state.web_search_result = "Web search tool not available."
                return state

            result = self.web_search.search(state)

            if result and getattr(result, 'success', False):
                state.web_search_result = result.content
                if hasattr(result, 'sources') and result.sources:
                    state.sources.extend(result.sources)
            else:
                error_msg = getattr(result, 'error', 'Unknown error') if result else 'No result returned'
                state.web_search_result = f"No relevant information found through web search. Error: {error_msg}"
        except Exception as e:
            state.web_search_result = f"Error occurred during web search: {str(e)}"
        return state

    def summarizer_node(self, state: GraphState) -> GraphState:
        try:
            content = getattr(state, 'db_result', None) or getattr(state, 'web_search_result', None)
            if not content or content in [
                "No relevant information found through web search.",
                "Web search tool not available."
            ] or content.startswith("Error occurred during web search:") or content.startswith("No relevant information found through web search. Error:"):
                state.final_answer = (
                    "Sorry, I couldn't find relevant financial information for your query. "
                    "Please try rephrasing it or asking something else."
                )
                return state

            summarizer_state = GraphState(
                user_query=state.user_query,
                session_id=state.session_id,
                history=state.history,
                rephrased_query=state.rephrased_query,
                db_result=state.db_result,
                web_search_result=state.web_search_result,
                sources=state.sources
            )

            result = self.summarizer.summarize(summarizer_state)
            state.final_answer = result.summary
            if hasattr(result, 'sources') and result.sources:
                state.sources.extend(result.sources)
        except Exception:
            fallback = getattr(state, 'db_result', None) or getattr(state, 'web_search_result', None)
            if fallback and not fallback.startswith("Error") and not fallback.startswith("No relevant"):
                truncated_content = fallback[:500] + "..." if len(fallback) > 500 else fallback
                state.final_answer = f"Based on available information: {truncated_content}"
            else:
                state.final_answer = (
                    "An error occurred while processing your query. "
                    "Please try again with a different question."
                )
        return state

    def memory_node(self, state: GraphState) -> GraphState:
        try:
            return self.memory.save_interaction(state)
        except Exception:
            return state

    def out_of_scope_node(self, state: GraphState) -> GraphState:
        q = state.user_query.lower()
        if any(w in q for w in ['weather', 'climate']):
            state.final_answer = (
                "I specialize in financial topics. For weather, check Weather.com. "
                "However, if you want to know how weather impacts markets, I can help!"
            )
        elif any(w in q for w in ['recipe', 'cooking', 'food', 'eat']):
            state.final_answer = (
                "I focus on financial data and analysis. For recipes or food suggestions, try a food app. "
                "However, I can help with food industry investments, restaurant stocks, or agricultural commodities!"
            )
        elif any(w in q for w in ['doctor', 'medical']):
            state.final_answer = (
                "I offer financial expertise, not medical advice. "
                "But I can assist with health sector investments and pharmaceutical company reports."
            )
        else:
            state.final_answer = (
                "I'm FinanceGPT, your assistant for:\n"
                "• Stock analysis and market data\n"
                "• Company earnings and financial reports\n"
                "• Market trends and insights\n"
                "• Investment strategies\n"
                "Please ask a finance-related question."
            )
        return state

    def supervisor_router(self, state: GraphState) -> str:
        return state.route_decision or "intent"

    def intent_router(self, state: GraphState) -> str:
        return state.route_decision or "out_of_scope"

    def db_lookup_router(self, state: GraphState) -> str:
        return state.route_decision or "not_found"
