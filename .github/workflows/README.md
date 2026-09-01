# GitHub Actions are temporarily paused

The workflow definitions are preserved in `../workflows-disabled/` so pushes to
`main`, pull requests, and tags do not start GitHub Actions while the current
product-hardening pass is in progress.

To restore automation, move the three YAML files back into this directory:

```text
.github/workflows-disabled/*.yml -> .github/workflows/*.yml
```

Review their triggers before reactivation, then commit the moves.
