"""
DeepSeek LLM Service — chat and structured evaluation via OpenAI-compatible API.

Usage:
    llm = LLMService(settings)
    async for chunk in llm.chat(messages):
        print(chunk, end="")
    result = await llm.evaluate("I think the project is very good...")
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

from openai import AsyncOpenAI

# ── System prompts ───────────────────────────────────────────

SYSTEM_PROMPT_ALEX = """\
You are Alex, a friendly but professional English interview coach.
You conduct mock interviews for English learners. Your goals:
1. Ask one question at a time, related to the interview topic.
2. Keep questions clear and at an appropriate difficulty level.
3. Be encouraging but also push the candidate to elaborate.
4. After the user answers, briefly acknowledge their response, then ask the next question.
5. Use natural, conversational English.

Remember: this is a speaking practice session. Keep the conversation flowing naturally.
"""

EVAL_SYSTEM_PROMPT = """\
You are an expert English speaking evaluator. Given a transcript of a spoken English
conversation, evaluate the speaker's performance across multiple dimensions.
You must respond with a JSON object matching the evaluation schema.
Be fair but thorough in your assessment.
"""

EVAL_FUNCTION = {
    "name": "evaluate_speaking",
    "description": "Evaluate a spoken English transcript and return structured scores.",
    "parameters": {
        "type": "object",
        "properties": {
            "overall_score": {
                "type": "number",
                "description": "Overall score 0-100",
            },
            "pronunciation_score": {
                "type": "number",
                "description": "Pronunciation accuracy 0-100",
            },
            "fluency_score": {
                "type": "number",
                "description": "Fluency and pacing 0-100",
            },
            "vocabulary_score": {
                "type": "number",
                "description": "Vocabulary range and usage 0-100",
            },
            "grammar_score": {
                "type": "number",
                "description": "Grammar correctness 0-100",
            },
            "feedback": {
                "type": "string",
                "description": "Overall feedback summary",
            },
            "suggestions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific improvement suggestions",
            },
        },
        "required": [
            "overall_score",
            "pronunciation_score",
            "fluency_score",
            "vocabulary_score",
            "grammar_score",
            "feedback",
            "suggestions",
        ],
    },
}


class LLMService:
    """DeepSeek API wrapper (OpenAI-compatible)."""

    def __init__(self, config):
        self._config = config
        self._client = AsyncOpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
        )

    # ── Streaming chat ───────────────────────────────────────

    async def chat(
        self,
        messages: list[dict],
        stream: bool = True,
        model: str = "deepseek-chat",
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion tokens.

        Args:
            messages: List of {"role": ..., "content": ...} dicts.
            stream: Whether to stream tokens.
            model: Model identifier.

        Yields:
            str: Individual text chunks from the assistant.
        """
        # Ensure system prompt is present
        if not messages or messages[0].get("role") != "system":
            messages = [{"role": "system", "content": SYSTEM_PROMPT_ALEX}] + messages

        if stream:
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
            )
            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        else:
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False,
            )
            yield response.choices[0].message.content or ""

    # ── Structured evaluation via function calling ───────────

    async def evaluate(
        self,
        transcript: str,
        model: str = "deepseek-chat",
    ) -> dict:
        """
        Evaluate a speaking transcript and return structured scores.

        Args:
            transcript: The full transcript of the user's spoken answers.

        Returns:
            dict: Evaluation result with scores and feedback.
        """
        messages = [
            {"role": "system", "content": EVAL_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Please evaluate the following spoken English transcript. "
                    f"Return your evaluation using the evaluate_speaking function.\n\n"
                    f"Transcript:\n{transcript}"
                ),
            },
        ]

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            functions=[EVAL_FUNCTION],
            function_call={"name": "evaluate_speaking"},
        )

        msg = response.choices[0].message
        if msg.function_call and msg.function_call.arguments:
            return json.loads(msg.function_call.arguments)

        # Fallback: try to parse content as JSON
        if msg.content:
            return json.loads(msg.content)

        raise RuntimeError("LLM did not return evaluation results")
