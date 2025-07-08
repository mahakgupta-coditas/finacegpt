from app.schemas.query_schema import QueryRequest, QueryResponse
from app.langgraph.graph import FinanceGPTGraph
from app.langgraph.agents.memory_agent import MemoryAgent
from app.langgraph.state import GraphState

def process_query(payload: QueryRequest, db, vector_db_tool=None, web_search_tool=None):
    """Process query with proper error handling"""
    try:
        agent = MemoryAgent(db)
        history = agent.get_history(payload.session_id)

        state = GraphState(
            user_query=payload.query,
            session_id=payload.session_id,
            history=history
        )

        graph = FinanceGPTGraph(
            vector_db_tool=vector_db_tool,
            web_search_tool=web_search_tool,
            db=db
        )
        
        compiled_graph = graph.create_graph()
        result = compiled_graph.invoke(state.model_dump())

        final_answer = result.get("final_answer", "Unable to process query")
        
        return QueryResponse(
            answer=final_answer,
            sources=result.get("sources", [])
        )

    except Exception as e:
        return QueryResponse(
            answer="I encountered an error processing your request. Please try again.",
            sources=[]
        )