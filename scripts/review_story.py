"""Create an offline review artifact from one repository-owned story file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from storyboard_studio.cli import main as storyboard_main


def _inside(root: Path, candidate: Path, label: str) -> Path:
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside the checked-out repository") from exc
    return resolved


def review_story(source: Path, output_dir: Path, repository: Path) -> dict[str, object]:
    root = repository.resolve()
    input_path = _inside(root, root / source, "Story input")
    destination = _inside(root, root / output_dir, "Review output")
    if not input_path.is_file() or input_path.is_symlink():
        raise ValueError("Story input must be one existing, non-symlink repository file")
    if input_path.suffix.lower() not in {".json", ".md", ".markdown"}:
        raise ValueError("Story input must use .json, .md, or .markdown")
    destination.mkdir(parents=True, exist_ok=True)

    doctor_json = destination / "doctor.json"
    doctor_markdown = destination / "doctor.md"
    evidence_json = destination / "evidence.json"
    deck = destination / "review.pptx"
    commands = [
        ["doctor", str(input_path), "--format", "json", "--output", str(doctor_json)],
        ["doctor", str(input_path), "--format", "markdown", "--output", str(doctor_markdown)],
        ["evidence", str(input_path), "--output", str(evidence_json)],
        [
            "export",
            "--input",
            str(input_path),
            "--output",
            str(deck),
            "--format",
            "pptx",
            "--bundle",
            "--viewer-status",
            "ci-structural-review-only",
        ],
    ]
    for command in commands:
        if storyboard_main(command) != 0:
            raise RuntimeError(f"Review command failed: storyboard {' '.join(command)}")

    doctor = json.loads(doctor_json.read_text(encoding="utf-8"))
    evidence = json.loads(evidence_json.read_text(encoding="utf-8"))
    manifest = {
        "schema_version": "1",
        "input": input_path.relative_to(root).as_posix(),
        "network_provider_used": False,
        "factual_truth_verified": False,
        "doctor": doctor["summary"],
        "evidence": evidence["summary"],
        "artifacts": sorted(path.name for path in destination.iterdir() if path.is_file()),
    }
    manifest_path = destination / "review-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose and render one reviewed Storyboard story without an AI provider."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("storyboard-review"), type=Path)
    parser.add_argument("--repository", default=Path.cwd(), type=Path)
    args = parser.parse_args()
    try:
        manifest = review_story(args.input, args.output_dir, args.repository)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(f"Reviewed {manifest['input']} without a network provider; factual truth remains author-owned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
