from ckanext.bsi_restricted_resources.logic.access_helpers import (
    resource_access_level_choices
)


def test_resource_access_level_choices():
    for choice in resource_access_level_choices():
        label = choice.get("label")
        assert label is not None
        assert isinstance(label, str)
        assert len(label) > 0
        value = choice.get("value")
        assert value is not None
        assert isinstance(value, str)
        assert len(value) > 0
