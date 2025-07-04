from groq import Groq
from app.config.config import settings
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from typing import Type
import json
import re

class LLMService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def generate_response(self, prompt: str, parser: PydanticOutputParser, model: str = None) -> BaseModel:
        try:
            model = model or self.model
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful financial assistant. ALWAYS respond with ONLY valid JSON in the exact format requested. Do not include any explanatory text before or after the JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1024
            )
            response_text = response.choices[0].message.content.strip()
            try:
                return parser.parse(response_text)
            except Exception:
                json_data = self._extract_json_from_text(response_text)
                if json_data:
                    try:
                        return parser.pydantic_object(**json_data)
                    except Exception:
                        pass
                return self._get_default_response(parser.pydantic_object)
        except Exception:
            return self._get_default_response(parser.pydantic_object)

    def _extract_json_from_text(self, text: str) -> dict:
        try:
            text = re.sub(r'^.*?(?=\{)', '', text, flags=re.DOTALL)
            text = re.sub(r'\}.*?$', '}', text, flags=re.DOTALL)
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = text[json_start:json_end]
                return json.loads(json_str)
        except Exception:
            pass
        return None

    def _get_default_response(self, model_class: Type[BaseModel]) -> BaseModel:
        if model_class.__name__ == "SupervisorResponse":
            return model_class(decision="intent")
        elif model_class.__name__ == "IntentResponse":
            return model_class(intent="out_of_scope")
        elif model_class.__name__ == "RephraseResponse":
            return model_class(rephrased_query="financial query", original_query="financial query")
        elif model_class.__name__ == "DatabaseLookupResponse":
            return model_class(found=False)
        elif model_class.__name__ == "SummarizerResponse":
            return model_class(summary="Unable to process request at this time.", sources=[])
        else:
            return model_class()
