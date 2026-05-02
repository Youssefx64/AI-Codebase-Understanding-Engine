"""LLM client adapter — wraps the OpenAI SDK for async completions.

Uses Replit AI Integrations proxy when AI_INTEGRATIONS_OPENAI_BASE_URL is
set; falls back to the standard OpenAI endpoint otherwise.
"""

from typing import Optional

import openai

from core.config import get_settings
from core.exceptions import LLMError
from core.logging import get_logger
from domain.interfaces import ILLMClient

logger = get_logger(__name__)


def _build_client() -> openai.AsyncOpenAI:
    settings = get_settings()
    kwargs: dict = {"api_key": settings.effective_openai_api_key}
    base_url = settings.effective_openai_base_url
    if base_url:
        kwargs["base_url"] = base_url
    return openai.AsyncOpenAI(**kwargs)


class OpenAILLMClient(ILLMClient):
    """Async LLM client backed by the OpenAI chat completions API."""

    def __init__(self) -> None:
        self._client = _build_client()
        settings = get_settings()
        self._model = settings.llm_model
        logger.info("LLM client initialised", model=self._model)

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        """Send a completion request and return the response text."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except openai.APIError as exc:
            logger.error("LLM API error", error=str(exc))
            raise LLMError(str(exc)) from exc
        except Exception as exc:
            logger.error("Unexpected LLM error", error=str(exc))
            raise LLMError(str(exc)) from exc


# Module-level singleton
_client: Optional[OpenAILLMClient] = None


def get_llm_client() -> OpenAILLMClient:
    global _client
    if _client is None:
        _client = OpenAILLMClient()
    return _client
