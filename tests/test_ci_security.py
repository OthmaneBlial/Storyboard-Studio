from __future__ import annotations

import re
from pathlib import Path

WORKFLOW_FILES = tuple(sorted(Path(".github/workflows").glob("*.yml"))) + tuple(
    sorted(Path(".github/workflows-disabled").glob("*.yml"))
)
ACTION_REF = re.compile(r"uses:\s*([^\s]+)@([^\s#]+)")
SHA_REF = re.compile(r"^[0-9a-f]{40}$")


def test_external_workflow_actions_are_pinned_to_commit_shas() -> None:
    assert WORKFLOW_FILES

    mutable_refs: list[str] = []
    for workflow_path in WORKFLOW_FILES:
        for line_number, line in enumerate(
            workflow_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            match = ACTION_REF.search(line)
            if not match or match.group(1).startswith("./"):
                continue
            if not SHA_REF.fullmatch(match.group(2)):
                mutable_refs.append(f"{workflow_path}:{line_number}: {match.group(1)}@{match.group(2)}")

    assert not mutable_refs, "Mutable GitHub Action references found:\n" + "\n".join(mutable_refs)


def test_release_workflow_requires_green_ci_for_the_exact_commit() -> None:
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert 'gh run list --repo "$GH_REPO" --workflow ci.yml --commit "$TARGET_SHA"' in workflow
    for required_job in (
        "verify (3.10)",
        "verify (3.11)",
        "verify (3.12)",
        "verify (3.13)",
        "verify (3.14)",
        "package",
        "browser",
        "benchmark",
    ):
        assert f'"{required_job}"' in workflow
