"""One export gate for every caller of the PowerPoint renderer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from storyboard_studio.layout import LayoutContract, analyze_overflow
from storyboard_studio.schemas import PresentationPayload


class ExportPreflightError(ValueError):
    def __init__(self, report: dict[str, Any]):
        self.report = report
        messages = "; ".join(finding["message"] for finding in report["findings"])
        super().__init__(
            f"Export preflight failed: {messages} Shorten the text, choose focus layout or split the slide."
        )


def prepare_export(data: Mapping[str, Any], contract: LayoutContract) -> dict[str, Any]:
    presentation = PresentationPayload.model_validate(data).model_dump(mode="json")
    report = analyze_overflow(presentation, contract)
    if report["findings"]:
        raise ExportPreflightError(report)
    return presentation
