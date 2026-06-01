from pathlib import Path
from string import Formatter
from typing import Any


class PromptTemplateError(Exception):
    pass


class PromptTemplateService:
    def __init__(self, template_dir: Path | None = None) -> None:
        self.template_dir = template_dir or Path(__file__).resolve().parents[1] / "prompts"

    def load_template(self, template_name: str) -> str:
        template_path = self._template_path(template_name)
        if not template_path.exists():
            raise PromptTemplateError(f"Prompt template not found: {template_name}")
        return template_path.read_text(encoding="utf-8")

    def render(self, template_name: str, **variables: Any) -> str:
        template = self.load_template(template_name)
        missing = sorted(self._required_variables(template) - set(variables))
        if missing:
            missing_text = ", ".join(missing)
            raise PromptTemplateError(f"Missing prompt template variables for {template_name}: {missing_text}")
        return template.format(**variables)

    def _template_path(self, template_name: str) -> Path:
        normalized = template_name.strip()
        if not normalized:
            raise PromptTemplateError("Prompt template name is required.")
        if Path(normalized).name != normalized:
            raise PromptTemplateError(f"Prompt template name must not contain path separators: {template_name}")
        filename = normalized if normalized.endswith(".md") else f"{normalized}.md"
        return self.template_dir / filename

    def _required_variables(self, template: str) -> set[str]:
        variables: set[str] = set()
        for _literal, field_name, _format_spec, _conversion in Formatter().parse(template):
            if field_name:
                variables.add(field_name.split(".", 1)[0].split("[", 1)[0])
        return variables
