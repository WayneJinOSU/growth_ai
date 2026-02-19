from typing import List, Optional, Dict, Any, Type
import time
import json
from openai import OpenAI
from pydantic import BaseModel
import config

MAX_RETRIES = 2
RETRY_DELAY = 3


class LLMClient:
    def __init__(self):
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=config.OPENAI_API_KEY)
        self.model = "google/gemini-3-pro-preview"

    def _call_with_retry(self, fn, retries=MAX_RETRIES, delay=RETRY_DELAY):
        """通用重试包装：首次失败后等待 delay 秒再试一次。"""
        last_error = None
        for attempt in range(1, retries + 1):
            try:
                return fn()
            except Exception as e:
                last_error = e
                if attempt < retries:
                    print(f"  [LLM] Attempt {attempt} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
        print(f"  [LLM] All {retries} attempts failed: {last_error}")
        raise last_error

    def analyze_text(self, prompt: str, system_prompt: str = "You are a financial analyst.",
                     model="google/gemini-3-pro-preview") -> str:
        try:
            response = self._call_with_retry(lambda: self.client.chat.completions.create(
                model=model if model else self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            ))
            if response and response.choices and len(response.choices) > 0:
                return response.choices[0].message.content or ""
            return ""
        except Exception as e:
            print(f"LLM Error: {e}")
            return ""

    def extract_structured_data(self, prompt: str, schema: Type[BaseModel],
                                system_prompt: str = "You are a data extractor.") -> Optional[BaseModel]:
        try:
            completion = self._call_with_retry(lambda: self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                response_format=schema,
            ))
            if completion and completion.choices and len(completion.choices) > 0:
                return completion.choices[0].message.parsed
            return None
        except Exception as e:
            print(f"LLM Structure Error: {e}")
            return None

llmClient = LLMClient()

if __name__ == "__main__":
    rs = llmClient.analyze_text(prompt="What is your name?")
    print(rs)