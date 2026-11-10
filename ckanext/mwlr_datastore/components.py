"""What's new, and what this site is built from (MWDS-529).

The footer's DataStore version links to /whats-new: the release notes for
users, from a Markdown file the DataStore image bakes in, so the notes always
belong to the build that is running. Signed-in users also see every enabled
plugin, the package it comes from and its version or commit, read from the
installed packages at runtime - like mwlr_versions(), never a list kept by hand.
"""
import functools
import json
import logging
import re
import subprocess
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


TAG_LIKE = re.compile(r"^(v|release-|ckan-)?\d+(\.\d+)*$")


def _normalise_repo(url):
    url = re.sub(r"^git\+", "", url or "")
    url = re.sub(r"^git@github\.com:", "https://github.com/", url)
    return re.sub(r"\.git$", "", url).rstrip("/")


def _short(repo):
    return re.sub(r"^https://(github\.com|bitbucket\.org)/", "", repo)


def _link(repo, commit, tag):
    """A tag's release page, else the commit, else the repository."""
    github = repo.startswith("https://github.com/")
    if tag and github:
        return f"{repo}/releases/tag/{tag}"
    if commit and github:
        return f"{repo}/tree/{commit}"
    if commit and repo.startswith("https://bitbucket.org/"):
        return f"{repo}/src/{commit}"
    return repo


@functools.lru_cache(maxsize=None)
def git_checkout(path):
    """Repository, commit and exact tag of a source checkout, or None.

    The base image installs most extensions from git clones under /srv/app/src
    owned by another user, hence safe.directory. Read once per process: the
    image does not change under a running site.
    """
    def git(*args):
        out = subprocess.run(
            ["git", "-c", "safe.directory=*", "-C", path, *args],
            capture_output=True, text=True, timeout=5, check=False)
        return out.stdout.strip() if out.returncode == 0 else ""
    try:
        repo = _normalise_repo(git("config", "--get", "remote.origin.url"))
        commit = git("rev-parse", "HEAD")
        tag = git("describe", "--tags", "--exact-match")
    except (OSError, subprocess.SubprocessError):
        return None
    if not repo or not commit:
        return None
    return {"repo": repo, "commit": commit, "tag": tag}


def source_of(name, version, direct_url, checkout=git_checkout):
    """Where a package came from, and the page that says what is in it.

    direct_url is pip's record of an install from a URL (PEP 610), or None for
    an install from PyPI. A git install records the repository, the ref asked
    for and the commit it resolved to. A local install (the base image's git
    clones) is read from its checkout. Either way a tag links to its release
    page and anything else to the commit, and the ref shown is the tag or the
    short commit - which can differ from the package's own version when a
    project forgets to bump it.
    """
    if not direct_url:
        return {"source": "PyPI", "ref": version,
                "url": f"https://pypi.org/project/{name}/{version}/"}
    vcs = direct_url.get("vcs_info")
    if vcs:
        repo = _normalise_repo(direct_url.get("url", ""))
        commit = vcs.get("commit_id", "")
        requested = vcs.get("requested_revision") or ""
        tag = requested if TAG_LIKE.match(requested) else ""
        return {"source": _short(repo), "ref": requested or commit[:7],
                "url": _link(repo, commit, tag)}
    url = direct_url.get("url", "")
    info = checkout(url[len("file://"):]) if url.startswith("file://") else None
    if info:
        return {"source": _short(info["repo"]), "ref": info["tag"] or info["commit"][:7],
                "url": _link(info["repo"], info["commit"], info["tag"])}
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
