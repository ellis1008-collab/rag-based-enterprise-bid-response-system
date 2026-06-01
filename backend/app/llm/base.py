from abc import ABC, abstractmethod

from app.llm.schemas import ProviderTextResponse


class BaseLLMProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    async def invoke_text(self, prompt: str, prompt_type: str = "text") -> ProviderTextResponse:
        pass
