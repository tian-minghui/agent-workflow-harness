from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path


# A complete ${name} placeholder is eligible for replacement. Other shell-style
# text is intentionally untouched because the workflow contract does not use it.
TEMPLATE_PLACEHOLDER = re.compile(r"\$\{([^}]*)\}")
RESERVED_TEMPLATE_VARIABLES = frozenset({"workflowDir", "taskDir"})
TEMPLATE_VARIABLE_NAME = re.compile(r"^(?:workflowDir|taskDir|[a-z][a-z0-9_]*)$")


class TemplateError(ValueError):
    """Raised when a template placeholder cannot be validated or resolved."""


def _validate_template_name(name: str) -> None:
    if TEMPLATE_VARIABLE_NAME.fullmatch(name) is None:
        raise TemplateError(f"invalid template variable: {name}")


def extract_template_references(value: str) -> set[str]:
    """Validate complete placeholders and return the referenced variable names."""
    references: set[str] = set()
    for match in TEMPLATE_PLACEHOLDER.finditer(value):
        name = match.group(1)
        _validate_template_name(name)
        references.add(name)
    return references


def validate_template_syntax(value: str, field: str) -> None:
    try:
        extract_template_references(value)
    except TemplateError as error:
        raise TemplateError(f"{field}: {error}") from error


def substitute_template(value: str, variables: Mapping[str, str]) -> str:
    """Replace placeholders in one pass so replacement text is never reparsed."""
    parts: list[str] = []
    cursor = 0
    try:
        for match in TEMPLATE_PLACEHOLDER.finditer(value):
            name = match.group(1)
            _validate_template_name(name)
            if name not in variables:
                raise TemplateError(f"unresolved template variable: {name}")
            parts.append(value[cursor:match.start()])
            parts.append(variables[name])
            cursor = match.end()
    except TemplateError as error:
        raise TemplateError(error) from error
    parts.append(value[cursor:])
    return "".join(parts)


def template_variables(
    *,
    workflow_dir: Path | str,
    task_dir: str,
    inputs: Mapping[str, str],
) -> dict[str, str]:
    if not task_dir:
        raise TemplateError("task_dir is required")
    if any(name in RESERVED_TEMPLATE_VARIABLES for name in inputs):
        raise TemplateError("task input cannot override a reserved variable")
    variables = {"workflowDir": str(workflow_dir), "taskDir": task_dir}
    variables.update(inputs)
    return variables
