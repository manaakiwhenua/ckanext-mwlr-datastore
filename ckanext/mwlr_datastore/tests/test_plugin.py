"""Tests for plugin.py.

Run against a CKAN with this extension installed:

    pytest --ckan-ini=test.ini ckanext/mwlr_datastore
"""
import os

import pytest

from ckan.plugins import plugin_loaded

from ckanext.mwlr_datastore.plugin import MwlrDatastorePlugin


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_plugin_loads():
    assert plugin_loaded("mwlr_datastore")


def _versions(monkeypatch, **env):
    """mwlr_versions() with the build environment set to exactly `env`."""
    for key in ("VERSION_BUILD_NUMBER", "BUILD_NUMBER", "GIT_COMMIT_ID",
                "RELEASE_VERSION"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return MwlrDatastorePlugin().mwlr_versions()


def test_versions_reports_the_build_environment(monkeypatch):
    v = _versions(monkeypatch, VERSION_BUILD_NUMBER="349",
                  GIT_COMMIT_ID="d07a332757fd", RELEASE_VERSION="1.1.0")
    assert v["build"] == "349"
    assert v["commit"] == "d07a332757fd"
    assert v["release"] == "1.1.0"


def test_versions_are_empty_rather_than_invented(monkeypatch):
    """A local build has no build key and no release; the footer omits them.

    An invented version is the drift this reporting exists to prevent, so
    absent must stay absent rather than becoming "0.0.0" or "unknown".
    """
    v = _versions(monkeypatch)
    assert v["build"] == ""
    assert v["commit"] == ""
    assert v["release"] == ""


def test_versions_prefer_the_deployment_over_the_image(monkeypatch):
    """VERSION_BUILD_NUMBER is set per deployment and wins over the baked one."""
    v = _versions(monkeypatch, VERSION_BUILD_NUMBER="349", BUILD_NUMBER="348")
    assert v["build"] == "349"


def test_versions_read_ckan_and_the_extension_at_runtime(monkeypatch):
    """Never hardcoded - the point of MWDS-357 was a footer that cannot lie."""
    import ckan
    v = _versions(monkeypatch)
    assert v["ckan"] == ckan.__version__
    assert v["extension"] and v["extension"] != "unknown"
