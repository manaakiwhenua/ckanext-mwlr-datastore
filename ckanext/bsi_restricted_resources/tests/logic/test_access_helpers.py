from ckanext.bsi_restricted_resources.logic.access_helpers import (
    resource_access_level_choices,
    user_choices
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


def test_user_choices(user):
    choices = user_choices()
    assert len(choices) > 0, "choices should not be empty"
    by_value = { choice["value"]:choice for choice in choices }
    user_choice = by_value.get(user["id"])
    assert user_choice["label"] == user["email"], "user label should be equal to email"
