import json
from ckanext.bsi_restricted_resources.tests.fixtures import searchable_dataset
import pytest

pytestmark = pytest.mark.ckan_config(
    "ckan.plugins",
    "mwlr_datastore bsi_restricted_resources image_view",
)


def test_ui_search_hides_restricted_resource_metadata(app, searchable_dataset):
    dataset_id = searchable_dataset["dataset_id"]

    response = app.get("/dataset/", params={"q": f"id:{dataset_id}"})

    assert response.status_code == 200
    assert dataset_id in response.text, "The public dataset must appear in the search results."

    for value in searchable_dataset["confidential_values"]:
        assert value not in response.text, f"UI search exposed confidential resource metadata: {value!r}"


@pytest.mark.parametrize(
    "use_default_schema",
    [
        pytest.param(False, id="custom-schema"),
        pytest.param(True, id="default-schema"),
    ],
)
def test_package_search_hides_restricted_resource_metadata(app, searchable_dataset, use_default_schema):
    response = app.get(
        "/api/3/action/package_search",
        params={
            "q": f"id:{searchable_dataset['dataset_id']}",
            "use_default_schema": str(use_default_schema).lower(),
        },
    )

    assert response.status_code == 200
    payload = response.json
    assert payload["success"] is True

    results = payload["result"]["results"]
    assert len(results) == 1, "The public dataset must be indexed and discoverable."

    dataset = results[0]
    assert dataset["id"] == searchable_dataset["dataset_id"]

    resource_ids = {resource["id"] for resource in dataset["resources"]}
    assert searchable_dataset["public_resource"]["id"] in resource_ids, "Filtering must preserve accessible resources."

    serialised_result = json.dumps(dataset)

    for value in searchable_dataset["confidential_values"]:
        assert value not in serialised_result, f"package_search exposed confidential metadata: {value!r}"
