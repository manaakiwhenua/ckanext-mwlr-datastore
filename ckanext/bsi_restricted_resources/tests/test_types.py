from ckanext.bsi_restricted_resources.types import (
    ResourceAccessLevel
)


def test_resource_access_levels_have_labels():
    for variant in ResourceAccessLevel:
        label = variant.label()
        assert label is not None
        assert isinstance(label, str)
        assert len(label) > 0
