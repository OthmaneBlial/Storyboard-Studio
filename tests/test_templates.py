from storyboard_studio.templates import available_templates, load_template_catalog


def test_template_catalog_has_one_launched_workflow_and_three_dormant_contracts():
    catalog = load_template_catalog()

    assert [template.id for template in catalog.templates] == [
        "decision-brief",
        "project-alignment",
        "proposal",
        "incident-retrospective",
    ]
    assert [template.id for template in available_templates()] == ["decision-brief"]
    assert [template.id for template in available_templates(include_dormant=True)] == [
        "decision-brief",
        "project-alignment",
        "proposal",
        "incident-retrospective",
    ]


def test_every_template_role_maps_only_to_explicit_author_inputs():
    for template in load_template_catalog().templates:
        declared = set(template.input_contract)
        assert template.activation_gate
        assert all(set(role.source_fields) <= declared for role in template.story_roles)
        assert all(role.purpose for role in template.story_roles)
