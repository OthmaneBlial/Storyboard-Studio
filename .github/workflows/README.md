# GitHub Actions

The active definitions in this directory run CI, reviewed-story checks and
tagged release preparation for pushes, pull requests and tags. The copies in
`../workflows-disabled/` are retained as a historical reference for audit and
rollback; they can intentionally differ from the active files when a later
change (for example, an expensive coverage gate) has not been copied into the
paused snapshot. Editing only that directory does not change GitHub Actions.

External actions in both active workflows and preserved snapshots are pinned to
immutable commit SHAs, with the human-readable release tag kept in a comment.
The monthly Dependabot GitHub Actions update is the review path for refreshing
those pins; verify the resolved commit and rerun the complete CI workflow before
merging an update.

Before changing a workflow, review its triggers, permissions and job names.
The required branch checks must match the active job names, and a release is
not considered published until the exact remote run and downloaded artifacts
are verified.

The active CI also builds the Dockerfile with a synthetic private-path sentinel,
checks the configured non-root user, starts the loopback service, and renders a
real demo export. The release gate includes this `container` job alongside the
Python, package, browser, and benchmark jobs; a passing definition alone is not
publication evidence.
