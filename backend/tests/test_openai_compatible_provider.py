import pytest

from app.llm.openai_compatible import OpenAICompatibleProvider, extract_json_from_text


def test_extract_json_from_pure_json() -> None:
    assert extract_json_from_text('{"status":"ok","count":2}') == {"status": "ok", "count": 2}


def test_extract_json_from_markdown_json_block() -> None:
    content = """Here is the result:

```json
{"status":"ok","items":[1,2,3]}
```
"""

    assert extract_json_from_text(content) == {"status": "ok", "items": [1, 2, 3]}


def test_extract_json_from_embedded_object() -> None:
    content = '模型回复：{"match_status":"satisfied","risk_level":"low"}，请查收。'

    assert extract_json_from_text(content) == {"match_status": "satisfied", "risk_level": "low"}


def test_extract_json_failure_has_clear_message() -> None:
    with pytest.raises(ValueError, match="Unable to parse JSON from model response"):
        extract_json_from_text("this response does not contain json")


def test_openai_compatible_provider_builds_chat_completions_url() -> None:
    provider = OpenAICompatibleProvider(
        base_url="http://localhost:11434/v1",
        api_key=None,
        model_name="llama3.1",
        temperature=0.2,
        max_tokens=1024,
    )

    assert provider._chat_completions_url() == "http://localhost:11434/v1/chat/completions"
