import zipfile

import pytest

from scripts.validate_distribution import REQUIRED, validate_distribution


def test_distribution_rejects_private_files_even_when_runtime_data_is_present(tmp_path):
    archive = tmp_path / "fixture.whl"
    for bad in ["output/private.zip", ".env", "secrets/private.key", "../outside.py"]:
        with zipfile.ZipFile(archive, "w") as output:
            for name in REQUIRED:
                output.writestr(name, "fixture")
            output.writestr(bad, "synthetic private sentinel")
        with pytest.raises(ValueError, match="Forbidden"):
            validate_distribution(archive)


def test_distribution_requires_the_complete_installed_studio(tmp_path):
    archive = tmp_path / "fixture.whl"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("storyboard_studio/cli.py", "fixture")
    with pytest.raises(ValueError, match="Missing"):
        validate_distribution(archive)


def test_source_archive_rejects_absolute_paths_and_links(tmp_path):
    import io
    import tarfile

    archive = tmp_path / "fixture.tar.gz"
    for name, linked in [("/absolute/file", False), ("root/../outside", False), ("root/link", True)]:
        with tarfile.open(archive, "w:gz") as output:
            member = tarfile.TarInfo(name)
            if linked:
                member.type = tarfile.SYMTYPE
                member.linkname = "/etc/passwd"
                output.addfile(member)
            else:
                member.size = 1
                output.addfile(member, io.BytesIO(b"x"))
        with pytest.raises(ValueError, match="Forbidden"):
            validate_distribution(archive)
