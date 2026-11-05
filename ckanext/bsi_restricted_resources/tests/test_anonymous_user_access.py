"""
Test anonymous access to datasets and fully restricted resources.
An anonymous (not logged in) user should be able to view public datasets and resources, but not private ones.

Run these tests with:
    ./bin/shell
    cd /srv/app/src_extensions/ckanext-mwlr-datastore
    pytest -v ckanext/bsi_restricted_resources/tests/test_anonymous_user_access.py

Note that these tests do clean the database, and you may need to compose down and up again to be able to login afterwards. You may also need to reindex Solr:

./bin/ckan search-index rebuild

"""

import json
import pytest
from ckanext.bsi_restricted_resources.tests.fixtures import dataset_urls


pytestmark = pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore bsi_restricted_resources")

# Parametize names the parameters on the first line, and each pytest.param provides a set of those values.

# When each pytest.param is passed to the test function 'test_anonymous_user_access', the fixture 'dataset_urls' uses 'dataset_is_private' and 'resource_access_level' (it names these values as parameters, so they're automatically passed in by pytest).

# The test uses 'url_key' to look up the appropriate URL in the dataset_urls dictionary provided by the 'dataset_urls' fixture, and uses the 'expected_http_status' and 'explanation' for the response.


@pytest.mark.parametrize(
    "dataset_is_private, resource_access_level, url_key, expected_http_status, explanation",
    [
        pytest.param(
            False,
            "dataset_access_level",
            "dataset_page",
            200,
            "Anonymous users must be able to view a public dataset.",
            id="public-dataset-with-public-resource",
        ),
        pytest.param(
            False,
            "restrict_to_owner",
            "dataset_page",
            200,
            "Anonymous users must be able to view a public dataset page even if the dataset contains private resources.",
            id="public-dataset-with-private-resource",
        ),
        pytest.param(
            False,
            "dataset_access_level",
            "resource_page",
            200,
            "Anonymous users must be able to view a public resource in a public dataset.",
            id="public-resource-in-public-dataset",
        ),
        pytest.param(
            False,
            "restrict_to_owner",
            "resource_page",
            403,
            "Anonymous users must not have access to a private resource in a public dataset.",
            id="private-resource-in-public-dataset",
        ),
        pytest.param(
            False,
            "dataset_access_level",
            "resource_api",
            200,
            "Anonymous users must be able to view a public resource API in a public dataset.",
            id="public-resource-api-in-public-dataset",
        ),
        pytest.param(
            False,
            "restrict_to_owner",
            "resource_api",
            403,
            "Anonymous users must not have access to a private resource API in a public dataset.",
            id="private-resource-api-in-public-dataset",
        ),
        pytest.param(
            True,
            "dataset_access_level",
            "dataset_page",
            404,
            "Anonymous users must not be able to view a private dataset.",
            id="private-dataset-with-public-resource",
        ),
        pytest.param(
            True,
            "restrict_to_owner",
            "resource_page",
            404,  # Returns a 404 rather than a 403as we first hit the privacy level of the dataset
            "Anonymous users must not have access to a private resource in a private dataset.",
            id="private-resource-in-private-dataset",
        ),
        pytest.param(
            True,
            "dataset_access_level",
            "resource_page",
            404,  # Returns a 404 rather than a 403as we first hit the privacy level of the dataset
            "Anonymous users must not have access to a public resource in a private dataset.",
            id="public-resource-in-private-dataset",
        ),
        pytest.param(
            True,
            "restrict_to_owner",
            "resource_api",
            403,
            "A public resource setting must not expose a private dataset's resource API.",
            id="public-resource-api-in-private-dataset",
        ),
        pytest.param(
            True,
            "restrict_to_owner",
            "resource_api",
            403,
            "Anonymous users must not have access to a private resource API in a private dataset.",
            id="private-resource-api-in-private-dataset",
        ),
    ],
)
def test_anonymous_user_access(app, dataset_urls, url_key, expected_http_status, explanation):

    url = dataset_urls["urls"][url_key]
    response = app.get(url)

    assert response.status_code == expected_http_status, (
        f"{explanation}. Fetched from {url}. Expected HTTP {expected_http_status}, received HTTP {response.status_code}"
    )


# Previously having an issue where there was a bare 403 page without the Datastore layout
# Test that accessing a private resource page as an anonymous user returns a proper CKAN 403 page
@pytest.mark.parametrize(
    "dataset_is_private, resource_access_level",
    [pytest.param(False, "restrict_to_owner", id="private-resource-in-public-dataset")],
)
def test_private_resource_page_give_CKAN_403_page(app, dataset_urls):
    response = app.get(dataset_urls["urls"]["resource_page"])

    assert response.status_code == 403
    assert response.content_type == "text/html; charset=utf-8"
    assert "You are not authorised to access this resource." in response.text
    assert "Traceback (most recent call last)" not in response.text


# Test that accessing a private resource API as an anonymous user returns a JSON error response
@pytest.mark.parametrize(
    "dataset_is_private, resource_access_level",
    [pytest.param(False, "restrict_to_owner", id="private-resource-in-public-dataset")],
)
def test_private_resource_api_returns_json_error(app, dataset_urls):
    response = app.get(dataset_urls["urls"]["resource_api"])

    assert response.status_code == 403
    assert response.content_type == "application/json;charset=utf-8"

    payload = response.json

    assert payload["success"] is False
    assert isinstance(payload["error"], dict)
    assert payload["error"]["message"], "The API denial must include a non-empty error message."
    assert "result" not in payload, "A denied API request must not return resource metadata."


# Test that accessing a public resource API as an anonymous user returns the requested resource
@pytest.mark.parametrize(
    "dataset_is_private, resource_access_level",
    [pytest.param(False, "dataset_access_level", id="public-resource-in-public-dataset")],
)
def test_public_resource_api_returns_requested_resource(app, dataset_urls):
    response = app.get(dataset_urls["urls"]["resource_api"])

    assert response.status_code == 200
    assert response.content_type == "application/json;charset=utf-8"

    payload = response.json

    assert payload["success"] is True
    assert payload["result"]["id"] == dataset_urls["ids"]["resource_id"]


@pytest.mark.parametrize(
    "dataset_is_private, resource_access_level",
    [pytest.param(False, "restrict_to_owner", id="private-resource-in-public-dataset")],
)
def test_package_show_hides_restricted_resource_metadata(app, dataset_urls):

    response = app.get(dataset_urls["urls"]["dataset_api"])
    assert response.status_code == 200
    payload = response.json

    assert payload["success"] is True
    assert payload["result"]["id"] == dataset_urls["ids"]["dataset_id"]

    serialised_result = json.dumps(payload["result"])

    for value in dataset_urls["resource_values"]:
        assert value not in serialised_result, f"package_show exposed confidential metadata: {value!r}"
