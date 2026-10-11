from collections.abc import Sequence

from openai import AsyncOpenAI, OpenAIError
from openai.types.chat import ChatCompletionMessageParam

from app.services.exceptions import LLMError


class LLMService:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        max_tokens: int,
        temperature: float = 0.2,
    ) -> None:
        self._client = client
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    async def complete(self, messages: Sequence[ChatCompletionMessageParam]) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=list(messages),
                max_tokens=self._max_tokens,  # required, or OpenRouter may return 402
                temperature=self._temperature,
            )
        except OpenAIError as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc

        if not response.choices:
            raise LLMError("LLM provider returned no choices")
        content = response.choices[0].message.content
        if not content or not content.strip():
            raise LLMError("LLM provider returned an empty answer")
        return content.strip()