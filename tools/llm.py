from typing import List, Optional, Dict, Any, Type
import json
from openai import OpenAI
from pydantic import BaseModel
import config

class LLMClient:
    def __init__(self):
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1",api_key=config.OPENAI_API_KEY)
        self.model = "google/gemini-3-pro-preview" # or gpt-4-turbo

    def analyze_text(self, prompt: str, system_prompt: str = "You are a financial analyst.") -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            if response and response.choices and len(response.choices) > 0:
                return response.choices[0].message.content or ""
            return ""
        except Exception as e:
            print(f"LLM Error: {e}")
            return ""

    def extract_structured_data(self, prompt: str, schema: Type[BaseModel], system_prompt: str = "You are a data extractor.") -> Optional[BaseModel]:
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                response_format=schema,
            )
            if completion and completion.choices and len(completion.choices) > 0:
                return completion.choices[0].message.parsed
            return None
        except Exception as e:
            print(f"LLM Structure Error: {e}")
            return None

