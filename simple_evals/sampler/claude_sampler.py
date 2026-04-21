"""Backward-compatibility shim.

The original ``ClaudeCompletionSampler`` wrapped the Anthropic SDK. Anthropic
was removed project-wide and replaced with OpenAI GPT-4o, so this module now
re-exports ``ChatCompletionSampler`` under the ``ClaudeCompletionSampler`` name
and ignores any Anthropic-specific arguments. This keeps ``simple_evals/simple_evals.py``
compiling without changes.
"""
from __future__ import annotations

from ..types import MessageList, SamplerBase, SamplerResponse
from .chat_completion_sampler import ChatCompletionSampler, OPENAI_SYSTEM_MESSAGE_API

# Kept for import compatibility — now an OpenAI-style system message.
CLAUDE_SYSTEM_MESSAGE_LMSYS = OPENAI_SYSTEM_MESSAGE_API


class ClaudeCompletionSampler(ChatCompletionSampler):
    """Legacy name — routes to OpenAI GPT-4o under the hood.

    Any Claude model name passed in is silently remapped to ``gpt-4o``.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        system_message: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ):
        if not model or model.startswith("claude"):
            model = "gpt-4o"
        super().__init__(
            model=model,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens,
        )
