import hashlib
import math
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx


class BaseEmbeddingProvider(ABC):
    provider_name: str
    dimension: int

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        pass

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class MockEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "mock"

    def __init__(self, dimension: int = 1024) -> None:
        self.dimension = dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token, weight in _weighted_tokens(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], byteorder="big") % self.dimension
            vector[index] += weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class OpenAICompatibleEmbeddingProvider(BaseEmbeddingProvider):
    provider_name = "openai-compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        model_name: str,
        timeout_seconds: int = 60,
    ) -> None:
        if not base_url:
            raise ValueError("Embedding base_url is required for openai-compatible provider.")
        if not model_name:
            raise ValueError("Embedding model_name is required for openai-compatible provider.")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.dimension = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        payload: dict[str, Any] = {"model": self.model_name, "input": texts}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(self._embeddings_url(), json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            detail = _compact_error_text(exc.response.text)
            raise ValueError(
                f"OpenAI-compatible embeddings request failed with status {exc.response.status_code}: {detail}"
            ) from exc
        except httpx.RequestError as exc:
            raise ValueError(f"OpenAI-compatible embeddings request failed: {exc}") from exc
        except ValueError as exc:
            raise ValueError("OpenAI-compatible embeddings response was not valid JSON.") from exc

        embeddings = _parse_embeddings(data, expected_count=len(texts))
        self.dimension = len(embeddings[0]) if embeddings else 0
        return embeddings

    def _embeddings_url(self) -> str:
        if self.base_url.endswith("/embeddings"):
            return self.base_url
        return f"{self.base_url}/embeddings"


def _weighted_tokens(text: str) -> list[tuple[str, float]]:
    raw_terms = re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]+", text.lower())
    weighted_tokens: dict[str, float] = {}
    for term in raw_terms:
        if _is_cjk(term):
            _add_token(weighted_tokens, term, 1.0)
            max_ngram = min(8, len(term))
            min_ngram = 1 if len(term) == 1 else 2
            for size in range(min_ngram, max_ngram + 1):
                for index in range(0, len(term) - size + 1):
                    _add_token(weighted_tokens, term[index : index + size], 1.0 + size / 2)
        else:
            _add_token(weighted_tokens, term, 3.0)
    return list(weighted_tokens.items())


def _add_token(weighted_tokens: dict[str, float], token: str, weight: float) -> None:
    if not token:
        return
    weighted_tokens[token] = max(weighted_tokens.get(token, 0.0), weight)


def _is_cjk(text: str) -> bool:
    return bool(text) and all("\u4e00" <= char <= "\u9fff" for char in text)


def _parse_embeddings(data: object, expected_count: int) -> list[list[float]]:
    if not isinstance(data, dict):
        raise ValueError("Embeddings response must be a JSON object.")

    items = data.get("data")
    if not isinstance(items, list):
        raise ValueError("Embeddings response did not include a data array.")

    sorted_items = sorted(
        enumerate(items),
        key=lambda item: item[1].get("index", item[0]) if isinstance(item[1], dict) else item[0],
    )
    embeddings: list[list[float]] = []
    for _position, item in sorted_items:
        if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
            raise ValueError("Embeddings response item did not include an embedding array.")
        embeddings.append([float(value) for value in item["embedding"]])

    if len(embeddings) != expected_count:
        raise ValueError("Embeddings response count did not match request count.")
    return embeddings


def _compact_error_text(text: str) -> str:
    compact = " ".join(text.split())
    return compact[:500] if compact else "empty error response"
