"""Public command-line interface for the complete Storyboard Studio package."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from generate_pptx import create_presentation
from schemas import PresentationPayload
from storyboard_studio import __version__
from storyboard_studio.doctor import diagnose_presentation, diagnosis_to_markdown
from storyboard_studio.resources import demo_outline_path


def _read_outline(path: Path) -> PresentationPayload:
    with path.open(encoding="utf-8") as file:
        return PresentationPayload.model_validate(json.load(file))


def _write_text(path: Path | None, content: str) -> None:
    if path is None:
        print(content, end="" if content.endswith("\n") else "\n")
        return
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Created {path}")


def _run_export(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        payload = _read_outline(args.input)
        destination = create_presentation(payload.model_dump(), args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not create the presentation: {exc}")
    print(f"Created {destination}")
    return 0


def _run_demo(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    args.input = demo_outline_path()
    result = _run_export(args, parser)
    print("Demo source: packaged synthetic product brief (no network or API key used).")
    return result


def _run_doctor(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        report = diagnose_presentation(_read_outline(args.input))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not diagnose the outline: {exc}")
    content = (
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.format == "json"
        else diagnosis_to_markdown(report)
    )
    _write_text(args.output, content)
    return 1 if args.fail_on_findings and report["findings"] else 0


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
    export.set_defaults(handler=lambda args: _run_export(args, parser))

    demo = commands.add_parser("demo", help="Export the packaged no-key synthetic demo deck.")
    demo.add_argument("--output", default=Path("storyboard-demo.pptx"), type=Path)
    demo.set_defaults(handler=lambda args: _run_demo(args, parser))

    doctor = commands.add_parser("doctor", help="Diagnose narrative structure and evidence gaps.")
    doctor.add_argument("input", type=Path)
    doctor.add_argument("--format", choices=("json", "markdown"), default="markdown")
    doctor.add_argument("--output", type=Path)
    doctor.add_argument("--fail-on-findings", action="store_true")
    doctor.set_defaults(handler=lambda args: _run_doctor(args, parser))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
