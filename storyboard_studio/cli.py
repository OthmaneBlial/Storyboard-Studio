"""Public command-line interface for the complete Storyboard Studio package."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from generate_pptx import create_presentation
from schemas import DecisionBriefV2
from storyboard_studio import __version__
from storyboard_studio.doctor import diagnose_story, diagnosis_to_markdown
from storyboard_studio.receipt import (
    create_receipt,
    diff_stories,
    diff_to_markdown,
    digest_value,
    verify_receipt,
)
from storyboard_studio.resources import demo_outline_path
from storyboard_studio.story import build_decision_story, read_story_or_presentation


def _write_text(path: Path | None, content: str) -> None:
    if path is None:
        print(content, end="" if content.endswith("\n") else "\n")
        return
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Created {path}")


def _write_json(path: Path, value: object) -> None:
    _write_text(path, json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n")


def _run_export(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        story, migrated = read_story_or_presentation(args.input)
        output = args.output.expanduser().resolve()
        if args.bundle:
            story_path = output.with_suffix(".story.json")
            _write_json(story_path, story.model_dump(mode="json"))
            outline_digest = digest_value(story.presentation.model_dump(mode="json"))
            provenance = (
                f"Storyboard Studio {__version__}; story schema {story.schema_version}; "
                f"outline sha256 {outline_digest}; integrity does not prove factual truth."
            )
            destination = create_presentation(story.presentation.model_dump(), output, provenance=provenance)
            receipt_path = output.with_suffix(".receipt.json")
            receipt = create_receipt(story, story_path, destination)
            _write_json(receipt_path, receipt)
            print(f"Created review bundle receipt {receipt_path}")
            if migrated:
                print("Wrapped the v1 freeform outline explicitly; no decision fields were inferred.")
        else:
            destination = create_presentation(story.presentation.model_dump(), output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not create the presentation: {exc}")
    print(f"Created {destination}")
    return 0


def _run_demo(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    args.input = demo_outline_path()
    result = _run_export(args, parser)
    print("Demo source: packaged guided decision story (no network or API key used).")
    return result


def _run_doctor(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        story, migrated = read_story_or_presentation(args.input)
        report = diagnose_story(story)
        report["input_format"] = "presentation-v1" if migrated else "story-v2"
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not diagnose the outline: {exc}")
    content = (
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.format == "json"
        else diagnosis_to_markdown(report)
    )
    _write_text(args.output, content)
    return 1 if args.fail_on_findings and report["findings"] else 0


def _run_migrate(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        story, migrated = read_story_or_presentation(args.input)
        if not migrated:
            parser.error("The input is already a story schema v2 document.")
        _write_json(args.output, story.model_dump(mode="json"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not migrate the outline: {exc}")
    return 0


def _run_compile(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        with args.input.open(encoding="utf-8") as file:
            brief = DecisionBriefV2.model_validate(json.load(file))
        story = build_decision_story(brief, args.theme)
        _write_json(args.output, story.model_dump(mode="json"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not compile the decision brief: {exc}")
    return 0


def _run_verify(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        result = verify_receipt(args.receipt.expanduser().resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not verify the receipt: {exc}")
    content = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    _write_text(args.output, content)
    return 0 if result["status"] == "verified" else 1


def _run_diff(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        old, old_migrated = read_story_or_presentation(args.old)
        new, new_migrated = read_story_or_presentation(args.new)
        if old_migrated or new_migrated:
            parser.error("Migrate v1 outlines before diffing so schema interpretation is explicit.")
        report = diff_stories(old, new)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not compare the stories: {exc}")
    content = (
        json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n"
        if args.format == "json"
        else diff_to_markdown(report)
    )
    _write_text(args.output, content)
    return 0


def _run_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("server:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="storyboard",
        description="Diagnose, review, and render local-first editable PowerPoint storyboards.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve", help="Run the complete local browser studio.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8000, type=int)
    serve.add_argument("--reload", action="store_true", help="Reload source changes during development.")
    serve.set_defaults(handler=_run_serve)

    export = commands.add_parser("export", help="Render a validated Storyboard JSON file to PPTX.")
    export.add_argument("--input", required=True, type=Path)
    export.add_argument("--output", default=Path("storyboard.pptx"), type=Path)
    export.add_argument(
        "--bundle",
        action="store_true",
        help="Also write a versioned story and verifiable Narrative Receipt.",
    )
    export.set_defaults(handler=lambda args: _run_export(args, parser))

    demo = commands.add_parser("demo", help="Export the packaged no-key guided decision demo.")
    demo.add_argument("--output", default=Path("storyboard-demo.pptx"), type=Path)
    demo.add_argument("--bundle", action="store_true", help="Write demo story and receipt files too.")
    demo.set_defaults(handler=lambda args: _run_demo(args, parser))

    doctor = commands.add_parser("doctor", help="Diagnose narrative structure and evidence gaps.")
    doctor.add_argument("input", type=Path)
    doctor.add_argument("--format", choices=("json", "markdown"), default="markdown")
    doctor.add_argument("--output", type=Path)
    doctor.add_argument("--fail-on-findings", action="store_true")
    doctor.set_defaults(handler=lambda args: _run_doctor(args, parser))

    migrate = commands.add_parser(
        "migrate", help="Explicitly wrap a legacy v1 presentation as a v2 freeform story."
    )
    migrate.add_argument("input", type=Path)
    migrate.add_argument("--output", required=True, type=Path)
    migrate.set_defaults(handler=lambda args: _run_migrate(args, parser))

    compile_story = commands.add_parser(
        "compile", help="Compile an author-supplied decision brief into a schema v2 story."
    )
    compile_story.add_argument("--input", required=True, type=Path)
    compile_story.add_argument("--output", required=True, type=Path)
    compile_story.add_argument(
        "--theme",
        choices=("midnight", "glacier", "ember", "forest", "royal", "sakura"),
        default="midnight",
    )
    compile_story.set_defaults(handler=lambda args: _run_compile(args, parser))

    verify = commands.add_parser("verify", help="Verify receipt structure and local artifact hashes.")
    verify.add_argument("receipt", type=Path)
    verify.add_argument("--output", type=Path)
    verify.set_defaults(handler=lambda args: _run_verify(args, parser))

    story_diff = commands.add_parser("diff", help="Compare two schema v2 stories.")
    story_diff.add_argument("old", type=Path)
    story_diff.add_argument("new", type=Path)
    story_diff.add_argument("--format", choices=("json", "markdown"), default="markdown")
    story_diff.add_argument("--output", type=Path)
    story_diff.set_defaults(handler=lambda args: _run_diff(args, parser))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
