"""
Production adapter for Google Gemini API.

Wraps all Gemini-specific logic behind AIServiceInterface.
Includes retry logging and safe JSON parsing.
"""

import json
import logging

import google.generativeai as genai

from infrastructure.ai.base import AIServiceInterface
from core.errors import ExternalServiceError

logger = logging.getLogger(__name__)


class GeminiAIService(AIServiceInterface):
    """Production adapter for Google Gemini API."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)
        logger.info("GeminiAIService initialised with model=%s", model_name)

    def generate_text(self, prompt: str) -> str:
        """Generate free-form text from a prompt."""
        try:
            logger.info("Gemini text request (prompt_length=%d)", len(prompt))
            response = self._model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error("Gemini API failed: %s", e)
            raise ExternalServiceError(f"AI service unavailable: {e}")

    def generate_json(self, prompt: str) -> list[dict]:
        """Generate structured JSON from a prompt."""
        raw = self.generate_text(prompt)
        # Strip markdown code fences Gemini sometimes wraps around JSON
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("Gemini returned invalid JSON: %s", raw[:200])
            raise ExternalServiceError(f"AI returned invalid JSON: {e}")
