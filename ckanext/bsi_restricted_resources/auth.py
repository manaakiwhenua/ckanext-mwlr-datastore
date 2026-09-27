import ckan.plugins.toolkit as tk

# Auth functions have the same names as the actions they are authorizing

def request_access_to_dataset_resources(context, data_dict):
    user = context.get("user")
    if not user:
        return {"success": False, "msg": "Login required"}
    package_id = data_dict.get("package_id")
    try:
        tk.check_access("package_show", context, {"id": package_id})
    except tk.NotAuthorized:
        return {"success": False, "msg": "Not authorised"}
    return {"success": True}

def get_auth_functions():
    return {
        "request_access_to_dataset_resources": request_access_to_dataset_resources,
    }
