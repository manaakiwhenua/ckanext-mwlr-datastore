"""Tests for the readiness endpoint (MWDS-378).

Run against a CKAN with this extension and ckanext-scheming installed:

    pytest --ckan-ini=test.ini ckanext/mwlr_datastore
"""
import pytest

from ckanext.mwlr_datastore import readiness

SCHEMA = "ckanext.mwlr_datastore:scheming/dataset.yaml"


@pytest.mark.ckan_config("ckan.plugins", "scheming_datasets mwlr_datastore")
@pytest.mark.ckan_config("scheming.dataset_schemas", SCHEMA)
@pytest.mark.usefixtures("with_plugins")
def test_ready_when_initialised(app):
    response = app.get(readiness.DEFAULT_PATH, status=200)
    assert response.json["ready"] is True
    assert set(response.json["checks"].values()) == {"ok"}
    assert "no-store" in response.headers["Cache-Control"]


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_not_ready_without_the_dataset_schema(app):
    """The failure names the check, so a probe log says what is wrong."""
    response = app.get(readiness.DEFAULT_PATH, status=503)
    assert response.json["ready"] is False
    assert response.json["checks"]["dataset_schema"] == "scheming_datasets is not loaded"
    assert response.json["checks"]["template_helpers"] == "ok"
    assert response.json["checks"]["template_renders"] == "ok"


@pytest.mark.ckan_config("ckan.plugins", "scheming_datasets mwlr_datastore")
@pytest.mark.ckan_config("scheming.dataset_schemas", SCHEMA)
@pytest.mark.ckan_config("ckanext.mwlr_datastore.readiness_path", "/custom/ready")
@pytest.mark.usefixtures("with_plugins")
def test_path_is_configurable(app):
    app.get("/custom/ready", status=200)
    app.get(readiness.DEFAULT_PATH, status=404)


@pytest.mark.ckan_config("ckan.plugins", "scheming_datasets mwlr_datastore")
@pytest.mark.ckan_config("scheming.dataset_schemas", SCHEMA)
@pytest.mark.usefixtures("with_plugins", "with_request_context")
def test_checks_touch_neither_database_nor_search(monkeypatch):
    """A dependency blip must not fail readiness - with one replica that is an
    outage the probe caused. Any database or Solr call from a check fails here."""
    import ckan.lib.search as search
    import ckan.model as model

    def refuse(*args, **kwargs):
        raise AssertionError("readiness called a dependency")

    # A context, so the patches are gone before CKAN's own fixtures tear down
    # through the database session.
    with monkeypatch.context() as patch:
        patch.setattr(model.Session, "execute", refuse)
        patch.setattr(model.Session, "query", refuse)
        patch.setattr(search, "query_for", refuse)
        patch.setattr(search, "make_connection", refuse)
        results = readiness.run_checks()

    assert results == {
        "dataset_schema": None,
        "template_helpers": None,
        "template_renders": None,
    }


def test_a_check_that_raises_reports_rather_than_500s(monkeypatch):
    def broken():
        raise RuntimeError("boom")

    monkeypatch.setattr(readiness, "CHECKS", (("broken", broken),))
    assert readiness.run_checks() == {"broken": "RuntimeError: boom"}
