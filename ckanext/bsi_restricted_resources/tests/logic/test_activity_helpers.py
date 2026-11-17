from ckanext.bsi_restricted_resources.logic import activity_helpers as helpers


def diff(old, new):
    return {"activities": [
        {"id": "old", "data": {"package": {"resources": old}}},
        {"id": "new", "data": {"package": {"resources": new}}},
    ]}


def test_access_changes_match_resources_and_ignore_order():
    old = [{"id": "a", "name": "Old", "resource_access_users": '[{"resource_grant_user_id":"1"}, {"resource_grant_user_id":"2"}]'},
           {"id": "deleted", "resource_access_users": [{"resource_grant_user_id": "3"}]}]
    new = [{"id": "a", "name": "New", "resource_access_users": [{"resource_grant_user_id": "2"}, {"resource_grant_user_id": "4"}]},
           {"id": "added", "resource_access_users": [{"resource_grant_user_id": "5"}]}]
    assert helpers.resource_access_activity_changes(diff(old, new)) == [
        {"resource_name": "New", "added": ["4"], "removed": ["1"]},
        {"resource_name": "added", "added": ["5"], "removed": []},
        {"resource_name": "deleted", "added": [], "removed": ["3"]},
    ]


def test_filter_preserves_other_grouped_fields(monkeypatch):
    changes = [{"type": "resource_extras", "method": "add_multiple", "key_list": [helpers.FIELD, "other"], "value_list": ["users", "value"]},
               {"type": "resource_extras", "key": helpers.FIELD}, {"type": "title"}]
    monkeypatch.setattr(helpers.tk.h, "compare_pkg_dicts", lambda *args: changes, raising=False)
    result = helpers.resource_access_other_changes(diff([], []))
    assert result[0]["key_list"] == ["other"]
    assert result[0]["value_list"]["other"] == "value"
    assert result[1] == {"type": "title"}
    assert changes[0]["key_list"] == [helpers.FIELD, "other"]
