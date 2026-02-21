"""
Safe JSON parser for LLM responses.
Handles markdown code blocks, leading/trailing text, and malformed output.
"""

import json
import re
from typing import Dict, Any, Optional


class JSONParser:
    """
    Utility for robustly parsing JSON from LLM response strings.
    """

    @staticmethod
    def parse_llm_json(response_text: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Safely parse JSON from an LLM response string.
        Strips markdown code blocks and handles common formatting errors.
        Returns default dict if parsing fails entirely.
        """
        if default is None:
            default = {}

        if not response_text or not isinstance(response_text, str):
            return default

        text = response_text.strip()

        # 1. Try direct parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. Try stripping markdown blocks
        if text.startswith("```json"):
            text = text.replace("```json", "", 1)
            if text.endswith("```"):
                text = text[:-3]
        elif text.startswith("```"):
            text = text.replace("```", "", 1)
            if text.endswith("```"):
                text = text[:-3]

        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 3. Aggressive regex fallback to find the first JSON object
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return default
