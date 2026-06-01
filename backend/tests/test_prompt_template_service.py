from pathlib import Path

import pytest

from app.services.prompt_template_service import PromptTemplateError, PromptTemplateService


def test_prompt_template_service_loads_template() -> None:
    template = PromptTemplateService().load_template("extract_requirements")

    assert "{rfp_text}" in template
    assert "{output_schema}" in template


def test_prompt_template_service_renders_variables(tmp_path: Path) -> None:
    template_dir = tmp_path / "prompts"
    template_dir.mkdir()
    (template_dir / "sample.md").write_text("Hello {name}, schema: {output_schema}", encoding="utf-8")

    rendered = PromptTemplateService(template_dir=template_dir).render(
        "sample",
        name="BidPilot",
        output_schema='{"type":"object"}',
    )

    assert rendered == 'Hello BidPilot, schema: {"type":"object"}'


def test_prompt_template_service_missing_variable_has_clear_error(tmp_path: Path) -> None:
    template_dir = tmp_path / "prompts"
    template_dir.mkdir()
    (template_dir / "sample.md").write_text("Hello {name}, {missing_value}", encoding="utf-8")

    with pytest.raises(PromptTemplateError, match="Missing prompt template variables for sample: missing_value"):
        PromptTemplateService(template_dir=template_dir).render("sample", name="BidPilot")


def test_prompt_template_service_missing_template_has_clear_error(tmp_path: Path) -> None:
    with pytest.raises(PromptTemplateError, match="Prompt template not found: not_found"):
        PromptTemplateService(template_dir=tmp_path).load_template("not_found")
