# Native preview builds

Storyboard Studio can be bundled as a single executable with an embedded
Python runtime. This is a convenience distribution for authors who should not
need to install Python; it is still the same local application and it does not
turn the product into a hosted service.

## Build the current platform

From a clean checkout with the development environment available:

```sh
make native-build
```

The `native` optional dependency installs PyInstaller. The specification at
[`packaging/storyboard-studio.spec`](../packaging/storyboard-studio.spec)
collects the package data and the `python-pptx` templates that are required at
runtime. The builder writes the executable and a digest report to
`output/native/`; generated build directories are intentionally ignored by
Git.

The builder verifies two facts before writing the report:

1. `storyboard-studio --version` matches the package version;
2. `storyboard-studio demo --output ...` creates a non-empty PPTX without a
   network request.

The report records the operating system, architecture, byte size and SHA-256.
Those values describe the exact local build and must be regenerated for every
release candidate. A local macOS result does not prove a Windows or Linux
binary.

## Release boundary

The native workflow under `.github/workflows/native.yml` builds preview
artifacts for the supported runner matrix on a version tag or manual dispatch.
Workflow artifacts are evidence for a candidate, not a public release. Before
attaching one to a GitHub release, a maintainer must verify the downloaded
artifact on the matching OS and architecture, including startup, demo/export,
clean user data, and uninstall/removal. Signing, notarization, quarantine and
antivirus behavior are platform-specific release gates and are not inferred
from a successful PyInstaller build.

Do not describe a native preview as signed, notarized, portable to another
architecture, or published on PyPI unless those facts have been independently
verified for the exact tag.
