from app.langgraph.state import GraphState
from datetime import datetime
from sqlalchemy import text

class MemoryAgent:
    def __init__(self, db):
        self.db = db
    
    def get_history(self, session_id: str) -> list[str]:
        """Retrieve chat history from the DB for a given session"""
        if not self.db:
            return []
        
        try:
            sql = text("""
                SELECT question, answer
                FROM memory_nodes
                WHERE session_id = :session_id
                ORDER BY created_at
            """)
            result = self.db.execute(sql, {"session_id": session_id})
            history = [f"Q: {row.question}\nA: {row.answer}" for row in result]
            return history
        except Exception:
            if self.db:
                self.db.rollback()
            return []
    
    def save_interaction(self, state: GraphState):
        """Save user interaction for future context"""
        if not self.db:
            return state
        
        try:
            # Initialize sources if not present
            if not hasattr(state, 'sources') or state.sources is None:
                state.sources = []
            
            # Initialize history if not present
            if not hasattr(state, 'history') or state.history is None:
                state.history = []
            
            interaction = {
                "session_id": state.session_id,
                "user_query": state.user_query,
                "final_answer": getattr(state, 'final_answer', ''),
                "timestamp": datetime.now(),
                "sources": ", ".join(state.sources) if state.sources else ""
            }
            
            sql = text("""
                INSERT INTO memory_nodes (session_id, question, answer, created_at, sources)
                VALUES (:session_id, :user_query, :final_answer, :timestamp, :sources)
            """)
            
            self.db.execute(sql, interaction)
            self.db.commit()
            
            state.history.append(f"Q: {state.user_query}")
            state.history.append(f"A: {state.final_answer}")
            
            return state
            
        except Exception:
            if self.db:
                self.db.rollback()
            return state