"""OpenAI-compatible / LangChain LLM client."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ...core.config import Settings
from ...core.logging import get_logger
from ...prompts import build_messages

logger = get_logger(__name__)


class LLMClient:
    """Async OpenAI-compatible chat client via LangChain."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._llm: ChatOpenAI | None = None
        if settings.llm_enabled:
            self._llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                timeout=settings.llm_timeout_s,
                model_kwargs={"response_format": {"type": "json_object"}},
            )

    @property
    def enabled(self) -> bool:
        return self._llm is not None

    async def generate_recommendation_json(
        self, context: dict[str, Any], data_gaps: list[str]
    ) -> dict[str, Any]:
        if not self._llm:
            raise RuntimeError("LLM is not enabled")

        messages = build_messages(context, data_gaps)
        lc_messages = []
        for m in messages:
            if m["role"] == "system":
                lc_messages.append(SystemMessage(content=m["content"]))
            else:
                lc_messages.append(HumanMessage(content=m["content"]))

        logger.info("Invoking LLM model=%s", self.settings.llm_model)
        result = await self._llm.ainvoke(lc_messages)
        content = result.content if isinstance(result.content, str) else str(result.content)
        return _extract_json(content)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        data = json.loads(text[start : end + 1])
        if isinstance(data, dict):
            return data
    raise ValueError("LLM did not return a JSON object")
