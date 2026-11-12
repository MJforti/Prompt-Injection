"""Prompt template validation and rendering.

Rendering uses literal placeholder replacement (not str.format), so documents
containing braces can never break or alter a template.
"""
from __future__ import annotations

from ..defaults import REQUIRED_TEMPLATE_KEYS

Message = dict[str, str]

# Placeholders each template MUST contain, so every strategy receives the same
# task and document (equivalent input conditions).
REQUIRED_PLACEHOLDERS = {
    "single": {"user": ("{task}", "{document}")},
    "two_stage": {"stage1_user": ("{document}",), "stage2_user": ("{task}", "{extracted}")},
}


class TemplateError(ValueError):
    """Raised when a strategy's templates are structurally invalid."""


def validate_templates(kind: str, templates: dict[str, str]) -> None:
    if kind not in REQUIRED_TEMPLATE_KEYS:
        raise TemplateError(f"unknown strategy kind: {kind}")
    for key in REQUIRED_TEMPLATE_KEYS[kind]:
        if not isinstance(templates.get(key), str) or not templates[key].strip():
            raise TemplateError(f"template '{key}' is required and must not be empty")
    unknown = set(templates) - set(REQUIRED_TEMPLATE_KEYS[kind])
    if unknown:
        raise TemplateError(f"unknown template keys: {', '.join(sorted(unknown))}")
    for key, placeholders in REQUIRED_PLACEHOLDERS[kind].items():
        for placeholder in placeholders:
            if placeholder not in templates[key]:
                raise TemplateError(f"template '{key}' must contain the placeholder {placeholder}")


def _fill(template: str, **values: str) -> str:
    # Single pass over the template so placeholder-like text inside a value
    # (e.g. a document containing "{task}") is never substituted again.
    result = []
    index = 0
    while index < len(template):
        for name, value in values.items():
            token = "{" + name + "}"
            if template.startswith(token, index):
                result.append(value)
                index += len(token)
                break
        else:
            result.append(template[index])
            index += 1
    return "".join(result)


def render_single(templates: dict[str, str], task: str, document: str) -> list[Message]:
    return [
        {"role": "system", "content": _fill(templates["system"], task=task, document=document)},
        {"role": "user", "content": _fill(templates["user"], task=task, document=document)},
    ]


def render_stage1(templates: dict[str, str], task: str, document: str) -> list[Message]:
    return [
        {"role": "system", "content": _fill(templates["stage1_system"], task=task, document=document)},
        {"role": "user", "content": _fill(templates["stage1_user"], task=task, document=document)},
    ]


def render_stage2(templates: dict[str, str], task: str, extracted: str) -> list[Message]:
    return [
        {"role": "system", "content": _fill(templates["stage2_system"], task=task, extracted=extracted)},
        {"role": "user", "content": _fill(templates["stage2_user"], task=task, extracted=extracted)},
    ]
