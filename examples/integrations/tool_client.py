"""Drive the agent-neutral JSONL tool server with the golden decision brief."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def call_tool(action: str, arguments: dict[str, object], request_id: str) -> dict[str, object]:
    request = {"id": request_id, "action": action, "arguments": arguments}
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "storyboard_studio.cli",
            "tools",
            "--workspace",
            str(ROOT),
            "--output-dir",
            "output/integrations/tool-server",
            "--once",
        ],
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError("Tool server process failed without a response")
    response = json.loads(process.stdout)
    if not response["ok"]:
        raise RuntimeError(f"{response['error']['code']}: {response['error']['message']}")
    return response["result"]


def main() -> int:
    brief = json.loads((ROOT / "examples/briefs/onboarding-decision.json").read_text(encoding="utf-8"))
    draft = call_tool("create_draft", {"brief": brief, "provider": "local"}, "draft")
    diagnosis = call_tool("diagnose", {"story": draft["story"]}, "doctor")
    digest = hashlib.sha256(json.dumps(draft["story"], sort_keys=True).encode()).hexdigest()[:8]
    rendered = call_tool(
        "render",
        {
            "story": draft["story"],
            "filename": f"onboarding-{digest}.pptx",
            "acknowledge_review_warnings": True,
        },
        "render",
    )
    print(
        json.dumps(
            {
                "artifact": rendered["artifact"],
                "doctor": diagnosis["diagnosis"]["summary"],
                "review": rendered["review"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
