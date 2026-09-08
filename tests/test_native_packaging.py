from pathlib import Path


def test_native_spec_collects_runtime_data_for_both_application_and_pptx() -> None:
    spec = Path("packaging/storyboard-studio.spec").read_text(encoding="utf-8")

    assert '"storyboard_studio", include_py_files=False' in spec
    assert 'collect_all("pptx", include_py_files=False)' in spec
    assert "include_py_files=False" in spec
    assert 'name="storyboard-studio"' in spec


def test_native_builder_exposes_a_helpful_cli_without_importing_pyinstaller() -> None:
    source = Path("scripts/build_native.py").read_text(encoding="utf-8")

    assert '"--output-dir"' in source
    assert '"--no-verify"' in source
    assert '"native-build.json"' in source
