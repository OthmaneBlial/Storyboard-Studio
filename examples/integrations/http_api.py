"""Use the golden decision brief through the local HTTP review surface."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "http://127.0.0.1:8000"


def request_json(path: str, body: object | None = None) -> dict[str, object]:
    data = None if body is None else json.dumps(body).encode()
    request = Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def main() -> int:
    brief = json.loads((ROOT / "examples/briefs/onboarding-decision.json").read_text(encoding="utf-8"))
    providers = request_json("/api/v1/providers")
    assert providers["default"] == "local"
    draft = request_json("/api/v1/stories/decision-brief", {"brief": brief, "theme": "midnight"})
    diagnosis = request_json("/api/v1/stories/doctor", draft["story"])
    bundle = request_json("/api/v1/bundles", draft["story"])
    output = ROOT / "output/integrations/http-onboarding-review.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(f"{BASE_URL}{bundle['download_url']}", timeout=30) as response:
        with output.open("xb") as file:
            file.write(response.read())
    print(
        json.dumps(
            {
                "artifact": str(output.relative_to(ROOT)),
                "doctor": diagnosis["summary"],
                "factual_truth_verified": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
