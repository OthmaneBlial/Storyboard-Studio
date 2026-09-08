# GitHub Actions

The active definitions in this directory run CI, reviewed-story checks and
tagged release preparation for pushes, pull requests and tags. The copies in
`../workflows-disabled/` are retained as a byte-for-byte reference for audit
and rollback; editing only that directory does not change GitHub Actions.

Before changing a workflow, review its triggers, permissions and job names.
The required branch checks must match the active job names, and a release is
not considered published until the exact remote run and downloaded artifacts
are verified.
