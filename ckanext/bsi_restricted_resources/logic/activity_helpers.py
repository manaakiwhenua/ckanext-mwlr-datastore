import json

import ckan.plugins.toolkit as tk

FIELD = "resource_access_users"


def _users(resource):
    value = resource.get(FIELD) or []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return set()
    if not isinstance(value, list):
        return set()
    return {item["resource_grant_user_id"] for item in value
            if isinstance(item, dict) and isinstance(item.get("resource_grant_user_id"), str)
            and item["resource_grant_user_id"]}


def resource_access_activity_changes(activity_diff):
    activities = activity_diff["activities"]
    packages = [activity.get("data", {}).get("package", {}) for activity in activities]
    resources = [{r["id"]: r for r in package.get("resources", [])
                  if isinstance(r, dict) and r.get("id")} for package in packages]
    result = []
    for resource_id in sorted(resources[0].keys() | resources[1].keys()):
        old, new = (version.get(resource_id, {}) for version in resources)
        before, after = _users(old), _users(new)
        if before == after:
            continue
        result.append({
            "resource_name": (new or old).get("name") or resource_id,
            "added": [user_id for user_id in sorted(after - before)],
            "removed": [user_id for user_id in sorted(before - after)]
        })
    return result


def resource_access_other_changes(activity_diff):
    activities = activity_diff["activities"]
    changes = tk.h.compare_pkg_dicts(activities[0]["data"]["package"],
                                     activities[1]["data"]["package"], activities[0]["id"])
    result = []
    for change in changes:
        if change.get("type") != "resource_extras":
            result.append(change)
        elif change.get("key") == FIELD:
            continue
        elif FIELD in change.get("key_list", []):
            change = dict(change)
            if change.get("method") == "add_multiple" and isinstance(change.get("value_list"), list):
                change["value_list"] = dict(zip(change["key_list"], change["value_list"]))
            change["key_list"] = [key for key in change["key_list"] if key != FIELD]
            if change["key_list"]:
                result.append(change)
        else:
            result.append(change)
    return result


def get_helpers():
    return {
        "resource_access_activity_changes": resource_access_activity_changes,
        "resource_access_other_changes": resource_access_other_changes,
    }
