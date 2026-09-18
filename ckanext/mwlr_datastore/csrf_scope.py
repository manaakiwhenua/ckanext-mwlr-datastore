"""Keep CKAN's CSRF exemptions to the request that made them (MWDS-477).

CKAN before 2.10.11 exempts a view from CSRF with ``csrf.exempt(dest)`` for
every request that is not session-authenticated, anonymous ones included.
Flask-WTF keeps exemptions in a set on a module-level object, so one anonymous
POST turns CSRF off for that view, for every user, until the worker restarts
(GHSA-mcvf-jxcw-vj73). Upstream fixed it with a class that exempts per request.

This wraps ``csrf.exempt`` so an exemption added while a request is served is
removed when that request ends. Exemptions made at start-up, outside any
request, are untouched. A CKAN that already has the upstream fix never calls
``csrf.exempt`` per request, so ``install`` does nothing there. Remove this
module once DataStore no longer runs a CKAN without the fix.
"""
from flask import g, has_request_context

_ADDED = "_mwlr_request_csrf_exemptions"


def install(app, csrf):
    """Scope ``csrf``'s per-request exemptions to their request on ``app``.

    ``csrf`` is CKAN's module-level object, shared by every app a process
    builds (the test suite builds many), so the wrapper goes on once and the
    clean-up is registered on each app.
    """
    if hasattr(csrf, "exempt_this_request"):
        return False

    if not getattr(csrf, "_mwlr_scoped", False):
        original = csrf.exempt

        def exempt(view):
            if not has_request_context():
                return original(view)
            before = set(csrf._exempt_views)
            result = original(view)
            added = set(csrf._exempt_views) - before
            if added:
                g.setdefault(_ADDED, set()).update(added)
            return result

        csrf.exempt = exempt
        csrf._mwlr_scoped = True

    if not getattr(app, "_mwlr_csrf_scoped", False):
        def drop_request_exemptions(_exc=None):
            for dest in g.pop(_ADDED, ()):
                csrf._exempt_views.discard(dest)

        app.teardown_request(drop_request_exemptions)
        app._mwlr_csrf_scoped = True
    return True
