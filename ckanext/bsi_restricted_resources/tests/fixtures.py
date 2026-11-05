import pytest
import ckan.plugins as plugins
from ckan.tests import factories
import ckan.plugins.toolkit as tk
from uuid import uuid4


@pytest.fixture
def dataset_urls(dataset_is_private, resource_access_level, with_plugins, clean_db, clean_index):
    assert plugins.plugin_loaded("bsi_restricted_resources"), (
        "Test setup failed: bsi_restricted_resources is not loaded."
    )

    organisation = factories.Organization()
    dataset = factories.Dataset(
        private=dataset_is_private,
        owner_org=organisation["id"],
    )

    resource_name_id = uuid4().hex
    resource_name = f"{resource_access_level}_resource_{resource_name_id}"
    resource_description = f"{resource_access_level}_description_{resource_name_id}"
    resource_url = f"https://example.invalid/file{resource_name_id}.csv"

    resource = factories.Resource(
        package_id=dataset["id"],
        resource_access_level=resource_access_level,
        name=resource_name,
        description=resource_description,
        url=resource_url,
    )

    dataset_dictionary = {
        "ids": {
            "dataset_id": dataset["id"],
            "resource_id": resource["id"],
        },
        "urls": {
            "dataset_api": tk.url_for("api.action", ver=3, logic_function="package_show", id=dataset["id"]),
            "resource_api": tk.url_for("api.action", ver=3, logic_function="resource_show", id=resource["id"]),
            "dataset_page": tk.url_for("dataset.read", id=dataset["id"]),
            "resource_page": tk.url_for(
                "dataset_resource.read",
                id=dataset["name"],
                resource_id=resource["id"],
            ),
        },
        "resource_values": [
            resource["name"],
            resource["description"],
            resource["url"],
        ],
    }

    return dataset_dictionary


@pytest.fixture
def searchable_dataset(with_plugins, clean_db, clean_index):
    assert plugins.plugin_loaded("bsi_restricted_resources")

    organisation = factories.Organization()
    dataset = factories.Dataset(
        private=False,
        owner_org=organisation["id"],
    )

    resource_name_id = uuid4().hex

    public_resource = factories.Resource(
        package_id=dataset["id"],
        name=f"publicresource{resource_name_id}",
        resource_access_level="dataset_access_level",
    )

    private_name = f"confidentialname{resource_name_id}"
    private_description = f"confidentialdescription{resource_name_id}"
    private_url = f"https://example.invalid/confidentialfile{resource_name_id}.csv"

    private_resource = factories.Resource(
        package_id=dataset["id"],
        name=private_name,
        description=private_description,
        url=private_url,
        resource_access_level="restrict_to_owner",
    )

    searchable_dataset_dictionary = {
        "dataset_id": dataset["id"],
        "public_resource": public_resource,
        "private_resource": private_resource,
        "confidential_values": [
            private_name,
            private_description,
            private_url,
        ],
    }

    return searchable_dataset_dictionary
