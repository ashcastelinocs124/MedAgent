"""Thin SamplerBase wrapper around the four-agent Pipeline for HealthBench.

Unlike the agentic-medbench PipelineSampler (which builds AgentTrace for
five-dimension grading), this sampler only produces an answer string —
exactly what HealthBenchEval's physician-rubric grading needs.

Threading: use n_threads=1 in HealthBenchEval (psycopg2 is not thread-safe).
"""
from __future__ import annotations

import asyncio
from typing import Any

from ..types import MessageList, SamplerBase, SamplerResponse
from src.personalization.models import HealthLiteracy, Sex, UserProfile


class PipelineHealthBenchSampler(SamplerBase):
    """Wraps Pipeline.run() as a SamplerBase for HealthBenchEval.

    Args:
        pipeline: An initialised Pipeline instance.
        user_profile: Optional UserProfile; defaults to a generic adult.
    """

    def __init__(
        self,
        pipeline: Any,
        user_profile: UserProfile | None = None,
    ) -> None:
        self.pipeline = pipeline
        self.user_profile = user_profile or UserProfile(
            age=40,
            sex=Sex.PREFER_NOT_TO_SAY,
            health_literacy=HealthLiteracy.MEDIUM,
        )

    @staticmethod
    def _extract_question(message_list: MessageList) -> str:
        """Extract the last user message as a plain string."""
        for msg in reversed(message_list):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            return part.get("text", "")
        return ""

    def __call__(self, message_list: MessageList) -> SamplerResponse:
        query = self._extract_question(message_list) or "No query provided."

        result = asyncio.run(self.pipeline.run(query, self.user_profile))

        return SamplerResponse(
            response_text=result.answer_text,
            actual_queried_message_list=list(message_list),
            response_metadata={"usage": None},
        )
