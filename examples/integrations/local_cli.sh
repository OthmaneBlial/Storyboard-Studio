#!/usr/bin/env bash
set -euo pipefail

project_root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$project_root"
mkdir -p output/integrations
storyboard_bin=${STORYBOARD_BIN:-.venv/bin/storyboard}
if [[ ! -x "$storyboard_bin" ]]; then
  echo "Run 'make setup' first or set STORYBOARD_BIN to an installed storyboard executable." >&2
  exit 1
fi

"$storyboard_bin" compile \
  --input examples/briefs/onboarding-decision.json \
  --output output/integrations/onboarding.story.json
"$storyboard_bin" doctor output/integrations/onboarding.story.json \
  --format markdown \
  --output output/integrations/onboarding.doctor.md
"$storyboard_bin" evidence output/integrations/onboarding.story.json \
  --output output/integrations/onboarding.evidence.json
"$storyboard_bin" export \
  --input output/integrations/onboarding.story.json \
  --output output/integrations/onboarding.pptx \
  --bundle \
  --viewer-status "not-run: local CLI example"

echo "Review output/integrations/onboarding.doctor.md before sharing the deck."
