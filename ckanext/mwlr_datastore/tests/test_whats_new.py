"""The What's new page and the footer links to it (MWDS-529).

Run against a CKAN with this extension installed:

    pytest --ckan-ini=test.ini ckanext/mwlr_datastore
"""
import pytest

import ckan.tests.factories as factories

from ckanext.mwlr_datastore import components


NOTES = "## 2.2.0 - 14 October 2026\n\n- Table previews have a new look.\n"


@pytest.fixture
def notes_file(tmp_path):
    path = tmp_path / "whats-new.md"
    path.write_text(NOTES, encoding="utf-8")
    return str(path)


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_whats_new_renders_the_baked_notes(app, notes_file, ckan_config, monkeypatch):
    monkeypatch.setitem(ckan_config, "ckanext.mwlr_datastore.whats_new_path", notes_file)
    body = app.get("/whats-new", status=200).body
    assert "14 October 2026" in body
    assert "Table previews have a new look." in body


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.ckan_config("ckanext.mwlr_datastore.whats_new_path", "/nonexistent/whats-new.md")
@pytest.mark.usefixtures("with_plugins")
def test_whats_new_without_notes_says_so(app):
    """A local build bakes no notes; the page says so rather than failing."""
    body = app.get("/whats-new", status=200).body
    assert "There are no release notes in this build." in body


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_versions_are_hidden_from_anonymous_users(app):
    body = app.get("/whats-new", status=200).body
    assert 'id="versions"' not in body


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("clean_db", "with_plugins")
def test_versions_show_for_signed_in_users(app):
    user = factories.User()
    token = factories.APIToken(user=user["name"])
    body = app.get("/whats-new", headers={"Authorization": token["token"]}, status=200).body
    assert 'id="versions"' in body
    assert "ckanext-mwlr-datastore" in body
    assert "docs.ckan.org" in body


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_footer_links_the_versions(app):
    body = app.get("/terms_of_use", status=200).body
    assert 'href="/whats-new"' in body
    assert "docs.ckan.org/en/" in body


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_components_lists_ckan_first_and_this_extension():
    rows = components.components()
    assert rows[0]["package"].lower() == "ckan"
    ours = [r for r in rows if r["package"] == "ckanext-mwlr-datastore"]
    assert ours and "mwlr_datastore" in ours[0]["plugins"]


def test_ckan_changelog_url_is_for_the_minor_version():
    assert components.ckan_changelog_url("2.12.0") == "https://docs.ckan.org/en/2.12/changelog.html"
    assert components.ckan_changelog_url("") == "https://docs.ckan.org/en/latest/changelog.html"


def test_a_git_tag_links_to_its_release_page():
    row = components.source_of("ckanext-mwlr-datastore", "2.2.0", {
        "url": "https://github.com/manaakiwhenua/ckanext-mwlr-datastore",
        "vcs_info": {"vcs": "git", "requested_revision": "v2.2.0", "commit_id": "abc1234def"},
    })
    assert row["url"] == "https://github.com/manaakiwhenua/ckanext-mwlr-datastore/releases/tag/v2.2.0"
    assert row["ref"] == "v2.2.0"


def test_a_git_commit_links_to_the_commit():
    row = components.source_of("ckanext-ldap", "3.2.0", {
        "url": "git+https://github.com/manaakiwhenua/ckanext-ldap.git",
        "vcs_info": {"vcs": "git", "requested_revision": "downstream", "commit_id": "0123456789abcdef"},
    })
    assert row["url"] == "https://github.com/manaakiwhenua/ckanext-ldap/tree/0123456789abcdef"
    assert row["source"] == "manaakiwhenua/ckanext-ldap"
    assert row["ref"] == "downstream"


def test_a_pypi_install_links_to_pypi():
    row = components.source_of("ckanext-scheming", "3.0.0", None)
    assert row["url"] == "https://pypi.org/project/ckanext-scheming/3.0.0/"


def test_a_local_install_without_a_checkout_has_no_link():
    row = components.source_of("ckanext-datapusher-plus", "2.0.0",
                               {"url": "file:///srv/app/src/x", "dir_info": {"editable": True}},
                               checkout=lambda path: None)
    assert row["url"] == ""
    assert row["source"] == "local"


def test_a_local_checkout_on_a_tag_links_to_the_release():
    """The base image's git clones: the tag, not the package version, which
    upstream sometimes forgets to bump (ckanext-pdfview 0.0.8 says 0.0.7)."""
    row = components.source_of("ckanext-pdfview", "0.0.7",
                               {"url": "file:///srv/app/src/ckanext-pdfview", "dir_info": {}},
                               checkout=lambda path: {"repo": "https://github.com/ckan/ckanext-pdfview",
                                                      "commit": "3acd4a5aaaa", "tag": "0.0.8"})
    assert row["url"] == "https://github.com/ckan/ckanext-pdfview/releases/tag/0.0.8"
    assert row["ref"] == "0.0.8"
    assert row["source"] == "ckan/ckanext-pdfview"


def test_a_local_checkout_off_a_tag_links_to_the_commit():
    row = components.source_of("ckanext-datapusher-plus", "2.0.0",
                               {"url": "file:///srv/app/src/ckanext-datapusher-plus", "dir_info": {}},
                               checkout=lambda path: {"repo": "https://github.com/manaakiwhenua/datapusher-plus",
                                                      "commit": "eefbc00ff60d", "tag": ""})
    assert row["url"] == "https://github.com/manaakiwhenua/datapusher-plus/tree/eefbc00ff60d"
    assert row["ref"] == "eefbc00"


def test_git_checkout_reads_a_real_repository(tmp_path):
    import subprocess
    repo = tmp_path / "ext"
    repo.mkdir()
    run = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)  # noqa: E731
    run("init", "-q")
    run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "c")
    run("tag", "v1.2.3")
    run("remote", "add", "origin", "git@github.com:ckan/ckanext-example.git")
    components.git_checkout.cache_clear()
    info = components.git_checkout(str(repo))
    assert info["repo"] == "https://github.com/ckan/ckanext-example"
    assert info["tag"] == "v1.2.3"
    assert len(info["commit"]) == 40
