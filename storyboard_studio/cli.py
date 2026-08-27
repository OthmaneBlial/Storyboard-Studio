"""Public command-line interface for the complete Storyboard Studio package."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from generate_pptx import create_presentation
from outline_markdown import story_to_markdown
from schemas import DecisionBriefV2
from storyboard_studio import __version__
from storyboard_studio.doctor import diagnose_story, diagnosis_to_markdown
from storyboard_studio.evidence import evidence_coverage
from storyboard_studio.layout import analyze_overflow, load_brand_kit, load_layout_contract
from storyboard_studio.receipt import (
    create_receipt,
    diff_stories,
    diff_to_markdown,
    digest_value,
    verify_receipt,
)
from storyboard_studio.resources import benchmark_suite_path, demo_outline_path
from storyboard_studio.story import build_decision_story, read_story_or_presentation
from storyboard_studio.templates import available_templates, template_catalog_to_markdown


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
        if args.brand_kit:
            story.presentation.brand_kit = load_brand_kit(args.brand_kit)
        if args.citations:
            story.presentation.citations_appendix = True
        output = args.output.expanduser().resolve()
        export_format = args.format
        if export_format == "auto":
            export_format = (
                "markdown"
                if output.suffix.lower() in {".md", ".markdown"}
                else "story-json"
                if output.suffix.lower() == ".json"
                else "pptx"
            )
        if export_format != "pptx":
            if args.bundle:
                parser.error("--bundle is available only for PPTX exports.")
            if args.theme_tokens:
                parser.error("--theme-tokens is available only for PPTX exports.")
            if export_format == "markdown":
                _write_text(output, story_to_markdown(story.model_dump(mode="json")))
            else:
                _write_json(output, story.model_dump(mode="json"))
            if migrated:
                print("Wrapped the legacy presentation explicitly; no decision fields were inferred.")
            return 0
        if args.bundle:
            story_path = output.with_suffix(".story.json")
            _write_json(story_path, story.model_dump(mode="json"))
            outline_digest = digest_value(story.presentation.model_dump(mode="json"))
            provenance = (
                f"Storyboard Studio {__version__}; story schema {story.schema_version}; "
                f"outline sha256 {outline_digest}; integrity does not prove factual truth."
            )
            destination = create_presentation(
                story.presentation.model_dump(),
                output,
                provenance=provenance,
                asset_root=args.input.parent,
                theme_tokens=args.theme_tokens,
            )
            receipt_path = output.with_suffix(".receipt.json")
            viewer_status = args.viewer_status.strip()
            if not viewer_status or len(viewer_status) > 240:
                parser.error("--viewer-status must contain between 1 and 240 characters.")
            receipt = create_receipt(
                story,
                story_path,
                destination,
                viewer_status=viewer_status,
            )
            _write_json(receipt_path, receipt)
            print(f"Created review bundle receipt {receipt_path}")
            if migrated:
                print("Wrapped the v1 freeform outline explicitly; no decision fields were inferred.")
        else:
            destination = create_presentation(
                story.presentation.model_dump(),
                output,
                asset_root=args.input.parent,
                theme_tokens=args.theme_tokens,
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not create the presentation: {exc}")
    print(f"Created {destination}")
    return 0


def _run_import(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        story, migrated = read_story_or_presentation(args.input)
        _write_json(args.output, story.model_dump(mode="json"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not import the story: {exc}")
    if migrated:
        print("Wrapped imported presentation content explicitly; no decision fields were inferred.")
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


def _run_templates(args: argparse.Namespace) -> int:
    templates = available_templates(include_dormant=args.all)
    content = (
        json.dumps(
            {
                "schema_version": "1",
                "templates": [template.model_dump(mode="json") for template in templates],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
        if args.format == "json"
        else template_catalog_to_markdown(templates)
    )
    _write_text(args.output, content)
    return 0


def _run_brand_kit(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        kit = load_brand_kit(args.input)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not validate the brand kit: {exc}")
    _write_text(
        args.output,
        json.dumps(
            {
                "status": "valid",
                "name": kit.name,
                "base_theme": kit.base_theme,
                "network_assets": 0,
                "contrast": "passed",
            },
            indent=2,
        )
        + "\n",
    )
    return 0


def _run_preflight(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        story, _ = read_story_or_presentation(args.input)
        contract = load_layout_contract(args.theme_tokens)
        result = analyze_overflow(story.presentation.model_dump(mode="json"), contract)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not preflight the presentation: {exc}")
    _write_text(args.output, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return 1 if args.fail_on_overflow and result["findings"] else 0


def _run_evidence(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        story, _ = read_story_or_presentation(args.input)
        report = evidence_coverage(story.presentation)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not analyze evidence coverage: {exc}")
    _write_text(args.output, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return 1 if args.fail_on_unresolved and report["summary"]["unresolved_claims"] else 0


def _run_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("server:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def _run_tools(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    from storyboard_studio.tool_server import ToolServer, serve_stdio

    try:
        server = ToolServer(args.workspace, args.output_dir)
    except (OSError, ValueError) as exc:
        parser.error(f"Could not start the local tool server: {exc}")
    return serve_stdio(server, once=args.once)


def _run_benchmark(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    from storyboard_studio.benchmark import run_benchmark

    try:
        report = run_benchmark(
            args.suite,
            args.output_dir,
            release=args.release,
            optional_provider=args.provider,
            allow_provider_network=args.allow_provider_network,
            baseline_path=args.baseline,
            overwrite=args.overwrite,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not run the benchmark: {exc}")
    print(f"Created benchmark report {args.output_dir.expanduser().resolve() / 'report.md'}")
    regression = report.get("regression", {})
    return 1 if args.fail_on_regression and regression.get("status") == "regressed" else 0


def _run_validate_contribution(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    from storyboard_studio.contributions import validate_contribution

    try:
        report = validate_contribution(
            args.manifest,
            args.output_dir,
            overwrite=args.overwrite,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not validate the contribution: {exc}")
    contribution_id = report["contribution"]["id"]
    print(f"Validated contribution {contribution_id!r} in {args.output_dir.expanduser().resolve()}")
    return 0


def _run_research_validate(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    from storyboard_studio.research import validate_research_session

    try:
        report = validate_research_session(args.input)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not validate the research session: {exc}")
    _write_json(args.output, report)
    return 0


def _run_research_aggregate(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    from storyboard_studio.research import aggregate_research_sessions

    try:
        report = aggregate_research_sessions(
            args.input_dir,
            args.output_dir,
            overwrite=args.overwrite,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not aggregate research sessions: {exc}")
    summary = report["summary"]
    assert isinstance(summary, dict)
    print(
        f"Created research aggregate for {summary['sessions']} validated sessions in "
        f"{args.output_dir.expanduser().resolve()}"
    )
    return 0


def _run_launch_check(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    from storyboard_studio.launch import inspect_launch_gate, write_launch_report

    try:
        report = inspect_launch_gate(
            args.repository,
            release_tag=args.release_tag,
            allow_network=args.allow_network,
        )
    except (OSError, ValueError, KeyError) as exc:
        parser.error(f"Could not inspect the launch gate: {exc}")
    write_launch_report(report, args.output, format=args.format)
    return 1 if args.fail_on_blocked and not report["launchable"] else 0


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

    tools = commands.add_parser(
        "tools", help="Run the agent-neutral local JSONL tool server on stdin/stdout."
    )
    tools.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Filesystem boundary for local evidence, receipts, and artifacts.",
    )
    tools.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/tools"),
        help="Artifact directory inside the workspace; existing files are never overwritten.",
    )
    tools.add_argument("--once", action="store_true", help="Handle one JSONL request and exit.")
    tools.set_defaults(handler=lambda args: _run_tools(args, parser))

    benchmark = commands.add_parser(
        "benchmark", help="Run the reproducible synthetic decision-story benchmark."
    )
    benchmark.add_argument("--suite", type=Path, default=benchmark_suite_path())
    benchmark.add_argument("--output-dir", type=Path, default=Path("output/benchmark"))
    benchmark.add_argument("--release", default=f"v{__version__}")
    benchmark.add_argument("--provider", choices=("gemini", "openai-compatible"), default="openai-compatible")
    benchmark.add_argument(
        "--allow-provider-network",
        action="store_true",
        help="Explicitly allow the configured optional provider; otherwise its lane is offline.",
    )
    benchmark.add_argument("--baseline", type=Path, help="Compare scores with a prior report.json.")
    benchmark.add_argument("--overwrite", action="store_true")
    benchmark.add_argument("--fail-on-regression", action="store_true")
    benchmark.set_defaults(handler=lambda args: _run_benchmark(args, parser))

    contribution = commands.add_parser(
        "validate-contribution",
        help="Validate privacy, license, schema, rendering, and attribution offline.",
    )
    contribution.add_argument("manifest", type=Path)
    contribution.add_argument("--output-dir", type=Path, default=Path("output/contribution-validation"))
    contribution.add_argument("--overwrite", action="store_true")
    contribution.set_defaults(handler=lambda args: _run_validate_contribution(args, parser))

    research = commands.add_parser(
        "research", help="Validate and aggregate anonymised consented research records locally."
    )
    research_commands = research.add_subparsers(dest="research_command", required=True)
    research_validate = research_commands.add_parser(
        "validate", help="Validate one private JSON session record without network access."
    )
    research_validate.add_argument("input", type=Path)
    research_validate.add_argument("--output", type=Path)
    research_validate.set_defaults(handler=lambda args: _run_research_validate(args, parser))
    research_aggregate = research_commands.add_parser(
        "aggregate", help="Aggregate private JSON session records into publishable summaries."
    )
    research_aggregate.add_argument("input_dir", type=Path)
    research_aggregate.add_argument("--output-dir", type=Path, default=Path("output/research"))
    research_aggregate.add_argument("--overwrite", action="store_true")
    research_aggregate.set_defaults(handler=lambda args: _run_research_aggregate(args, parser))

    launch_check = commands.add_parser(
        "launch-check", help="Inspect release and community gates without changing external state."
    )
    launch_check.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Repository root to inspect (default: current directory).",
    )
    launch_check.add_argument(
        "--release-tag",
        help="Expected exact release tag, such as v0.3.0; omitted means unverified.",
    )
    launch_check.add_argument(
        "--allow-network",
        action="store_true",
        help="Explicitly query public PyPI metadata; no other network call is made.",
    )
    launch_check.add_argument("--format", choices=("json", "markdown"), default="markdown")
    launch_check.add_argument("--output", type=Path)
    launch_check.add_argument("--fail-on-blocked", action="store_true")
    launch_check.set_defaults(handler=lambda args: _run_launch_check(args, parser))

    export = commands.add_parser(
        "export", help="Export a validated JSON or Markdown story to PPTX, Markdown, or story JSON."
    )
    export.add_argument("--input", required=True, type=Path)
    export.add_argument("--output", default=Path("storyboard.pptx"), type=Path)
    export.add_argument(
        "--format",
        choices=("auto", "pptx", "markdown", "story-json"),
        default="auto",
        help="Output format; auto infers Markdown/JSON from the output suffix and otherwise writes PPTX.",
    )
    export.add_argument(
        "--theme-tokens",
        type=Path,
        help="Use an explicit validated local layout-token file.",
    )
    export.add_argument(
        "--brand-kit",
        type=Path,
        help="Apply a validated local brand-kit JSON file without fetching fonts or assets.",
    )
    export.add_argument(
        "--citations",
        action="store_true",
        help="Append native citation slides containing author-checked evidence only.",
    )
    export.add_argument(
        "--bundle",
        action="store_true",
        help="Also write a versioned story and verifiable Narrative Receipt.",
    )
    export.add_argument(
        "--viewer-status",
        default="not-run",
        help="Record a completed viewer check in the bundle receipt (max 240 characters).",
    )
    export.set_defaults(handler=lambda args: _run_export(args, parser))

    import_story = commands.add_parser(
        "import", help="Import supported Markdown or JSON into a validated story-v2 JSON document."
    )
    import_story.add_argument("input", type=Path)
    import_story.add_argument("--output", required=True, type=Path)
    import_story.set_defaults(handler=lambda args: _run_import(args, parser))

    demo = commands.add_parser("demo", help="Export the packaged no-key guided decision demo.")
    demo.add_argument("--output", default=Path("storyboard-demo.pptx"), type=Path)
    demo.add_argument("--format", choices=("auto", "pptx"), default="pptx")
    demo.add_argument("--theme-tokens", type=Path)
    demo.add_argument("--brand-kit", type=Path)
    demo.add_argument("--citations", action="store_true")
    demo.add_argument("--bundle", action="store_true", help="Write demo story and receipt files too.")
    demo.add_argument(
        "--viewer-status",
        default="not-run",
        help="Record a completed viewer check in the bundle receipt (max 240 characters).",
    )
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

    templates = commands.add_parser(
        "templates", help="List launched narrative templates and their evidence-gated status."
    )
    templates.add_argument("--all", action="store_true", help="Include dormant template contracts.")
    templates.add_argument("--format", choices=("json", "markdown"), default="markdown")
    templates.add_argument("--output", type=Path)
    templates.set_defaults(handler=_run_templates)

    brand_kit = commands.add_parser("brand-kit", help="Validate a constrained local brand-kit JSON file.")
    brand_kit.add_argument("input", type=Path)
    brand_kit.add_argument("--output", type=Path)
    brand_kit.set_defaults(handler=lambda args: _run_brand_kit(args, parser))

    preflight = commands.add_parser("preflight", help="Check the shared layout budget before exporting.")
    preflight.add_argument("input", type=Path)
    preflight.add_argument("--theme-tokens", type=Path)
    preflight.add_argument("--output", type=Path)
    preflight.add_argument("--fail-on-overflow", action="store_true")
    preflight.set_defaults(handler=lambda args: _run_preflight(args, parser))

    evidence = commands.add_parser(
        "evidence", help="Report claim-to-source coverage without treating URLs as verification."
    )
    evidence.add_argument("input", type=Path)
    evidence.add_argument("--output", type=Path)
    evidence.add_argument("--fail-on-unresolved", action="store_true")
    evidence.set_defaults(handler=lambda args: _run_evidence(args, parser))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
