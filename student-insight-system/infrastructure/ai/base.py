"""
Abstract interface for AI text generation services.

All AI providers (Gemini, OpenAI, mock) implement this interface.
Services depend on this abstraction, never on a concrete provider.
"""

from abc import ABC, abstractmethod
from typing import Any


class AIServiceInterface(ABC):
    """Abstract interface for AI text generation."""

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """Generate free-form text from a prompt."""
        ...

    @abstractmethod
    def generate_json(self, prompt: str) -> list[dict[str, Any]]:
        """Generate structured JSON from a prompt."""
        ...
