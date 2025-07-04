from app.services.llm_call import LLMService
from app.langgraph.state import GraphState
from app.langgraph.pydantics import SummarizerResponse
from app.prompts.summarizer_prompt import SUMMARIZER_PROMPT
from langchain.output_parsers import PydanticOutputParser

class SummarizerAgent:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.parser = PydanticOutputParser(pydantic_object=SummarizerResponse)
        
    def summarize(self, state: GraphState) -> SummarizerResponse:
        """Summarize findings and create final answer"""
        try:
            # Get content from either db_result or web_search_result
            content = state.db_result or state.web_search_result or "No information found"
            
            # Create the prompt with the correct parameters
            prompt = SUMMARIZER_PROMPT.format(
                user_query=state.user_query,
                content=content,
                sources=state.sources or [],
                format_instructions=self.parser.get_format_instructions()
            )
            
            return self.llm_service.generate_response(prompt, self.parser)
            
        except Exception as e:
            print(f"[SummarizerAgent] Error: {e}")
            import traceback
            print(f"[SummarizerAgent] Traceback: {traceback.format_exc()}")
            
            # Return a fallback response
            return SummarizerResponse(
                summary="I apologize, but I encountered an error while processing your request. Please try again with a different question.",
                sources=state.sources or []
            )