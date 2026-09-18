"""CSRF exemptions last only for the request that made them (MWDS-477)."""
import pytest
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from ckanext.mwlr_datastore import csrf_scope


def _app_that_exempts(view):
    """A Flask app whose every request exempts ``view``, as CKAN 2.10.4 does
    for any request that is not session-authenticated."""
    app = Flask(__name__)
    csrf = CSRFProtect()
    assert csrf_scope.install(app, csrf)

    @app.before_request
    def exempt_for_this_request():
        csrf.exempt(view)

    app.add_url_rule("/form", "form", lambda: "", methods=["POST"])
    return app, csrf


def test_an_exemption_made_during_a_request_ends_with_it():
    app, csrf = _app_that_exempts("ckan.views.dataset.edit")
    app.test_client().post("/form")
    assert "ckan.views.dataset.edit" not in csrf._exempt_views


def test_start_up_exemptions_stay():
    app, csrf = _app_that_exempts("ckan.views.dataset.edit")
    csrf.exempt("ckan.views.api.action")
    app.test_client().post("/form")
    assert "ckan.views.api.action" in csrf._exempt_views


def test_a_request_does_not_remove_a_start_up_exemption_it_repeats():
    app, csrf = _app_that_exempts("ckan.views.api.action")
    csrf.exempt("ckan.views.api.action")
    app.test_client().post("/form")
    assert "ckan.views.api.action" in csrf._exempt_views


def test_nothing_to_do_where_ckan_already_exempts_per_request():
    class PerRequest(CSRFProtect):
        def exempt_this_request(self):
            pass

    assert csrf_scope.install(Flask(__name__), PerRequest()) is False


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_an_anonymous_post_leaves_no_exemption_behind(app):
    from ckan.config.middleware.flask_app import csrf

    before = set(csrf._exempt_views)
    app.post("/dataset/new", data={"name": "x"})
    assert set(csrf._exempt_views) == before
