"""Validated catalog of launched and evidence-gated narrative templates."""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from storyboard_studio.resources import template_catalog_path


class TemplateRole(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: str = Field(min_length=3, max_length=60)
    purpose: str = Field(min_length=3, max_length=180)
    source_fields: list[str] = Field(min_length=1, max_length=8)


class TemplateDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: Literal["decision-brief", "project-alignment", "proposal", "incident-retrospective"]
    name: str = Field(min_length=3, max_length=80)
    status: Literal["launched", "dormant"]
    job: str = Field(min_length=3, max_length=220)
    input_contract: list[str] = Field(min_length=3, max_length=20)
    story_roles: list[TemplateRole] = Field(min_length=3, max_length=8)
    activation_gate: str = Field(min_length=3, max_length=300)

    @model_validator(mode="after")
    def roles_only_use_declared_inputs(self) -> TemplateDefinition:
        declared = set(self.input_contract)
        referenced = {field for role in self.story_roles for field in role.source_fields}
        undeclared = referenced - declared
        if undeclared:
            raise ValueError(f"Template roles reference undeclared inputs: {sorted(undeclared)}")
        return self


class TemplateCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    templates: list[TemplateDefinition] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def launch_boundary_is_explicit(self) -> TemplateCatalog:
        identifiers = [template.id for template in self.templates]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Template identifiers must be unique.")
        launched = [template.id for template in self.templates if template.status == "launched"]
        if launched != ["decision-brief"]:
            raise ValueError(
                "Only decision-brief may be launched before external evidence supports expansion."
            )
        return self


def load_template_catalog() -> TemplateCatalog:
    with template_catalog_path().open(encoding="utf-8") as file:
        return TemplateCatalog.model_validate(json.load(file))


def available_templates(*, include_dormant: bool = False) -> list[TemplateDefinition]:
    templates = load_template_catalog().templates
    return templates if include_dormant else [item for item in templates if item.status == "launched"]


def template_catalog_to_markdown(templates: list[TemplateDefinition]) -> str:
    lines = ["# Storyboard Studio templates", ""]
    for template in templates:
        lines.extend(
            [
                f"## {template.name}",
                "",
                f"- ID: `{template.id}`",
                f"- Status: **{template.status}**",
                f"- Job: {template.job}",
                f"- Activation gate: {template.activation_gate}",
                "- Story roles: " + " → ".join(role.role for role in template.story_roles),
                "",
            ]
        )
    return "\n".join(lines)
