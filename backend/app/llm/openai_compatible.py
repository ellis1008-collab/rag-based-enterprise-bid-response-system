import json
import re
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from app.llm.base import BaseLLMProvider
from app.llm.schemas import ProviderTextResponse

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class OpenAICompatibleProvider(BaseLLMProvider):
    provider_name = "openai-compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        model_name: str,
        temperature: float,
        max_tokens: int,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def invoke_text(self, prompt: str, prompt_type: str = "text") -> ProviderTextResponse:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(self._chat_completions_url(), json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            detail = _compact_error_text(exc.response.text)
            raise ValueError(
                f"OpenAI-compatible API request failed with status {exc.response.status_code}: {detail}"
            ) from exc
        except httpx.RequestError as exc:
            raise ValueError(f"OpenAI-compatible API request failed: {exc}") from exc
        except ValueError as exc:
            raise ValueError("OpenAI-compatible API response was not valid JSON.") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Chat completions response did not include message content.") from exc

        if not isinstance(content, str):
            raise ValueError("Chat completions response content was not a string.")

        return ProviderTextResponse(content=content, raw_response=data)

    async def invoke_json(
        self,
        prompt: str,
        output_schema: type[SchemaT],
        prompt_type: str = "json",
    ) -> SchemaT:
        response = await self.invoke_text(prompt, prompt_type=prompt_type)
        parsed = extract_json_from_text(response.content)
        return output_schema.model_validate(parsed)

    def _chat_completions_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"


def extract_json_from_text(content: str) -> object:
    stripped = content.strip()
    if not stripped:
        raise ValueError("Unable to parse JSON from model response: response was empty.")

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    for fenced_content in re.findall(r"```(?:json)?\s*(.*?)```", content, flags=re.IGNORECASE | re.DOTALL):
        candidate = fenced_content.strip()
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    decoder = json.JSONDecoder()
    for index, char in enumerate(content):
        if char not in "{[":
            continue
        try:
            parsed, _end = decoder.raw_decode(content[index:])
            return parsed
        except json.JSONDecodeError:
            continue

    raise ValueError(
        "Unable to parse JSON from model response. Expected pure JSON, a markdown ```json block, "
        "or an embedded JSON object/array."
    )


def _compact_error_text(text: str) -> str:
    compact = " ".join(text.split())
    if not compact:
        return "empty error response"
    return compact[:500]
