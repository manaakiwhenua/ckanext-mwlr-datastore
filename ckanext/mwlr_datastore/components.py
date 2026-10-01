"""What's new, and what this site is built from (MWDS-529).

The footer's DataStore version links to /whats-new: the release notes for
users, from a Markdown file the DataStore image bakes in, so the notes always
belong to the build that is running. Signed-in users also see every enabled
plugin, the package it comes from and its version or commit, read from the
installed packages at runtime - like mwlr_versions(), never a list kept by hand.
"""
import json
import logging
import re
from importlib.metadata import distribution, entry_points

import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)

DEFAULT_WHATS_NEW_PATH = "/srv/app/whats-new.md"


def whats_new_path():
    return toolkit.config.get("ckanext.mwlr_datastore.whats_new_path") or DEFAULT_WHATS_NEW_PATH


def read_whats_new():
    """The release notes Markdown, or '' when the build has none (a local build)."""
    try:
        with open(whats_new_path(), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def ckan_changelog_url(version):
    """CKAN's changelog for the running minor version, e.g. 2.12."""
    m = re.match(r"(\d+)\.(\d+)", version or "")
    if not m:
        return "https://docs.ckan.org/en/latest/changelog.html"
    return f"https://docs.ckan.org/en/{m.group(1)}.{m.group(2)}/changelog.html"


def source_of(name, version, direct_url):
    """Where a package came from, and the page that says what is in it.

    direct_url is pip's record of an install from a URL (PEP 610), or None for
    an install from PyPI. A git install records the repository, the ref asked
    for and the commit it resolved to: a tag links to its release page, anything
    else to the commit. A local or editable install has no public page.
    """
    if not direct_url:
        return {"source": "PyPI", "ref": version,
                "url": f"https://pypi.org/project/{name}/{version}/"}
    vcs = direct_url.get("vcs_info")
    if vcs:
        repo = re.sub(r"^git\+", "", direct_url.get("url", ""))
        repo = re.sub(r"\.git$", "", repo)
        commit = vcs.get("commit_id", "")
        ref = vcs.get("requested_revision") or commit[:7]
        github = repo.startswith("https://github.com/")
        if ref and re.match(r"^v?\d+(\.\d+)*$", ref) and github:
            url = f"{repo}/releases/tag/{ref}"
        elif commit and github:
            url = f"{repo}/tree/{commit}"
        elif commit and repo.startswith("https://bitbucket.org/"):
            url = f"{repo}/src/{commit}"
        else:
            url = repo or ""
        return {"source": repo, "ref": ref, "url": url}
    return {"source": "local", "ref": version, "url": ""}


def _direct_url(dist):
    try:
        text = dist.read_text("direct_url.json")
        return json.loads(text) if text else None
    except (OSError, ValueError):
        return None


def components():
    """One row per installed package that provides an enabled plugin, CKAN first.

    Never raises: a page that lists versions must not fail because one package
    has odd metadata - that row is left out and logged instead.
    """
    enabled = toolkit.aslist(toolkit.config.get("ckan.plugins", ""))
    plugin_dist = {}
    try:
        for ep in entry_points(group="ckan.plugins"):
            if ep.name in enabled and ep.dist is not None:
                plugin_dist.setdefault(ep.name, ep.dist.metadata["Name"])
    except Exception:  # see the docstring
        log.exception("could not read the ckan.plugins entry points")

    by_package = {}
    for plugin in enabled:
        by_package.setdefault(plugin_dist.get(plugin, "ckan"), []).append(plugin)
    by_package.setdefault("ckan", [])

    rows = []
    for name, plugins in by_package.items():
        try:
            dist = distribution(name)
            version = dist.version
            if name.lower() == "ckan":
                row = {"source": "ckan/ckan", "ref": version, "url": ckan_changelog_url(version)}
            else:
                row = source_of(name, version, _direct_url(dist))
        except Exception:  # see the docstring
            log.exception("could not describe package %s", name)
            continue
        row.update({"package": name, "version": version, "plugins": sorted(plugins)})
        rows.append(row)
    rows.sort(key=lambda r: (r["package"].lower() != "ckan", r["package"].lower()))
    return rows


def show_components():
    """The component list is for signed-in users only: exact versions and
    commits make it easier to match the site against published advisories."""
    try:
        return bool(toolkit.current_user.is_authenticated)
    except Exception:  # no request context
        return False


def whats_new():
    return toolkit.render("whats_new.html", extra_vars={"notes": read_whats_new()})
