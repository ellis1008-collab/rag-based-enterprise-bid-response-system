import json
from time import perf_counter
from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_api_key_cipher
from app.llm.base import BaseLLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_compatible import OpenAICompatibleProvider, extract_json_from_text
from app.llm.schemas import LLMTextResult
from app.models import LLMCallLog, ModelConfig

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMService:
    def __init__(
        self,
        db: Session,
        model_config: ModelConfig | None = None,
        allow_fallback: bool = True,
    ) -> None:
        self.db = db
        self.model_config = model_config
        self.allow_fallback = allow_fallback

    async def invoke_text(self, prompt: str, prompt_type: str = "text") -> LLMTextResult:
        started_at = perf_counter()
        provider: BaseLLMProvider | None = None
        try:
            provider = self._build_provider()
            response = await provider.invoke_text(prompt, prompt_type=prompt_type)
            latency_ms = self._elapsed_ms(started_at)
            self._log_call(provider, prompt_type, latency_ms, success=True)
            return LLMTextResult(
                content=response.content,
                provider=provider.provider_name,
                model_name=provider.model_name,
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = self._elapsed_ms(started_at)
            self._log_call(provider, prompt_type, latency_ms, success=False, error_message=str(exc))
            raise

    async def invoke_json(
        self,
        prompt: str,
        output_schema: type[SchemaT],
        prompt_type: str = "json",
    ) -> SchemaT:
        schema_json = json.dumps(output_schema.model_json_schema(), ensure_ascii=False)
        json_prompt = (
            "Return only JSON that matches this JSON Schema:\n"
            f"```json\n{schema_json}\n```\n\n"
            f"Prompt:\n{prompt}"
        )

        started_at = perf_counter()
        provider: BaseLLMProvider | None = None
        try:
            provider = self._build_provider()
            response = await provider.invoke_text(json_prompt, prompt_type=prompt_type)
            parsed = self._parse_json_response(response.content)
            validated = output_schema.model_validate(parsed)
            latency_ms = self._elapsed_ms(started_at)
            self._log_call(provider, prompt_type, latency_ms, success=True)
            return validated
        except Exception as exc:
            latency_ms = self._elapsed_ms(started_at)
            self._log_call(provider, prompt_type, latency_ms, success=False, error_message=str(exc))
            raise

    def _build_provider(self) -> BaseLLMProvider:
        config = self.model_config or self._get_default_config()
        try:
            if config is None:
                raise ValueError("No enabled model config is available.")
            return self._provider_from_config(config)
        except ValueError:
            if self.allow_fallback:
                return MockLLMProvider()
            raise

    def _get_default_config(self) -> ModelConfig | None:
        default_config = self.db.scalar(
            select(ModelConfig)
            .where(ModelConfig.enabled.is_(True), ModelConfig.is_default.is_(True))
            .order_by(ModelConfig.updated_at.desc())
        )
        if default_config is not None:
            return default_config

        return self.db.scalar(
            select(ModelConfig)
            .where(ModelConfig.enabled.is_(True))
            .order_by(ModelConfig.created_at.desc())
        )

    def _provider_from_config(self, config: ModelConfig) -> BaseLLMProvider:
        if not config.enabled:
            raise ValueError("Model config is disabled.")

        provider_name = config.provider.strip().lower()
        if provider_name == "mock":
            return MockLLMProvider(model_name=config.model_name)

        if provider_name in {"openai-compatible", "openai_compatible"}:
            api_key = get_api_key_cipher().decrypt(config.api_key_encrypted)
            if not config.base_url or not config.model_name:
                raise ValueError("OpenAI-compatible config requires base_url and model_name.")
            return OpenAICompatibleProvider(
                base_url=config.base_url,
                api_key=api_key,
                model_name=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )

        raise ValueError(f"Unsupported provider: {config.provider}")

    def _parse_json_response(self, content: str) -> object:
        return extract_json_from_text(content)

    def _log_call(
        self,
        provider: BaseLLMProvider | None,
        prompt_type: str,
        latency_ms: int,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        provider_name = provider.provider_name if provider is not None else self._configured_provider_name()
        model_name = provider.model_name if provider is not None else self._configured_model_name()
        self.db.add(
            LLMCallLog(
                provider=provider_name,
                model_name=model_name,
                prompt_type=prompt_type,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message,
            )
        )
        self.db.commit()

    def _configured_provider_name(self) -> str:
        if self.model_config is not None:
            return self.model_config.provider
        return "unknown"

    def _configured_model_name(self) -> str:
        if self.model_config is not None:
            return self.model_config.model_name
        return "unknown"

    def _elapsed_ms(self, started_at: float) -> int:
        return max(0, round((perf_counter() - started_at) * 1000))
