"""
Deterministic mock AI service for testing.

Returns predictable responses — never makes external calls.
"""

from infrastructure.ai.base import AIServiceInterface


class MockAIService(AIServiceInterface):
    """Deterministic mock for testing — no external calls."""

    def generate_text(self, prompt: str) -> str:
        return (
            "<h3>Mock Insight Report</h3>"
            "<p>This is a deterministic test report.</p>"
        )

    def generate_json(self, prompt: str) -> list[dict]:
        return [
            {"title": "Mock Task 1", "description": "Test task", "days_to_complete": 5},
            {"title": "Mock Task 2", "description": "Test task", "days_to_complete": 3},
            {"title": "Mock Task 3", "description": "Test task", "days_to_complete": 7},
        ]
