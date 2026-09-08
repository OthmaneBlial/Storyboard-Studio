import ai_helper
import generate_pptx
import schemas
from storyboard_studio import ai_helper as packaged_ai_helper
from storyboard_studio import renderer as packaged_renderer
from storyboard_studio import schemas as packaged_schemas


def test_legacy_schema_module_is_a_compatibility_shim() -> None:
    assert schemas.PresentationPayload is packaged_schemas.PresentationPayload
    assert schemas.StoryDocumentV2 is packaged_schemas.StoryDocumentV2
    assert schemas.LocalAsset is packaged_schemas.LocalAsset
    assert packaged_schemas.PresentationPayload.__module__ == "storyboard_studio.schemas"
    assert ai_helper.build_local_presentation is packaged_ai_helper.build_local_presentation
    assert packaged_ai_helper.build_local_presentation.__module__ == "storyboard_studio.ai_helper"
    assert generate_pptx.create_presentation is packaged_renderer.create_presentation
    assert packaged_renderer.create_presentation.__module__ == "storyboard_studio.renderer"
