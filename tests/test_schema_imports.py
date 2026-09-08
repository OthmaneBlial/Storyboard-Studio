import schemas
from storyboard_studio import schemas as packaged_schemas


def test_legacy_schema_module_is_a_compatibility_shim() -> None:
    assert schemas.PresentationPayload is packaged_schemas.PresentationPayload
    assert schemas.StoryDocumentV2 is packaged_schemas.StoryDocumentV2
    assert schemas.LocalAsset is packaged_schemas.LocalAsset
    assert packaged_schemas.PresentationPayload.__module__ == "storyboard_studio.schemas"
