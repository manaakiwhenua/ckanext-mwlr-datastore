"""Tests for the tracking plugin's pieces that need no CKAN app.

    pytest --ckan-ini=test.ini ckanext/mwlr_tracking
"""
import pytest

import ckan.plugins as plugins

from ckanext.mwlr_tracking import plugin as tracking


class FakeApp(object):
    """Stands in for the Flask app the middleware wraps."""

    def __init__(self):
        self.hooks = []
        self.calls = []

    def after_request(self, fn):
        self.hooks.append(fn)
        return fn

    def __call__(self, environ, start_response):
        self.calls.append(environ.get('PATH_INFO'))
        return [b'ok']


class RecordingMiddleware(tracking.MwlrTrackingMiddleware):
    """The real middleware with the database call captured, not run."""

    def __init__(self, app, config):
        self.app = app
        self.config = config
        self.recorded = []

    def record_download(self, user_key, path):
        self.recorded.append((user_key, path))


def _mw(monkeypatch, active, config=None):
    monkeypatch.setattr(tracking, 'tracking_active', lambda cfg: active)
    return RecordingMiddleware(FakeApp(), config or {})


def test_middleware_delegates_unknown_attributes_to_the_app():
    # CKAN 2.11's core tracking plugin does app.after_request(...) on
    # whatever the previous IMiddleware returned, which is this object.
    app = FakeApp()
    mw = tracking.MwlrTrackingMiddleware.__new__(tracking.MwlrTrackingMiddleware)
    mw.app = app
    mw.config = {}
    def hook(response):
        return response
    mw.after_request(hook)
    assert app.hooks == [hook]


def test_request_always_reaches_the_app_when_tracking_is_off(monkeypatch):
    mw = _mw(monkeypatch, active=False)
    environ = {'PATH_INFO': '/dataset/abc/resource/def/download/file.csv'}
    assert mw(environ, None) == [b'ok']
    assert mw.app.calls == [environ['PATH_INFO']]
    assert mw.recorded == []


def test_download_is_recorded_and_request_passed_through(monkeypatch):
    mw = _mw(monkeypatch, active=True)
    path = '/dataset/0a1b/resource/2c3d/download/file.csv'
    environ = {'PATH_INFO': path, 'HTTP_USER_AGENT': 'ua', 'REMOTE_ADDR': '10.0.0.1'}
    assert mw(environ, None) == [b'ok']
    assert mw.recorded == [(tracking.visitor_key(environ), path)]
    assert mw.app.calls == [path]


def test_non_download_paths_are_not_recorded(monkeypatch):
    mw = _mw(monkeypatch, active=True)
    for path in ['/dataset/', '/dataset/0a1b/resource/2c3d', '/api/3/action/status_show']:
        mw({'PATH_INFO': path}, None)
    assert mw.recorded == []


def test_visitor_key_is_stable_and_tolerates_missing_headers():
    a = tracking.visitor_key({'HTTP_USER_AGENT': 'ua', 'REMOTE_ADDR': '1.2.3.4'})
    b = tracking.visitor_key({'HTTP_USER_AGENT': 'ua', 'REMOTE_ADDR': '1.2.3.4'})
    assert a == b and len(a) == 32
    assert tracking.visitor_key({}) != a


@pytest.mark.parametrize('config,loaded,expected', [
    ({'ckan.tracking_enabled': 'true'}, False, True),
    ({'ckan.tracking_enabled': 'false'}, False, False),
    ({}, False, False),
    ({}, True, True),
    ({'ckan.tracking_enabled': 'false'}, True, True),
])
def test_tracking_active_honours_setting_and_core_plugin(monkeypatch, config, loaded, expected):
    monkeypatch.setattr(plugins, 'plugin_loaded', lambda name: loaded and name == 'tracking')
    assert tracking.tracking_active(config) is expected


@pytest.mark.parametrize('data,expected', [
    ({'tracking_summary': {'total': 7, 'recent': 2}}, {'total': 7, 'recent': 2}),
    ({'tracking_summary': {}}, {'total': 0, 'recent': 0}),
    ({'tracking_summary': None}, {'total': 0, 'recent': 0}),
    ({}, {'total': 0, 'recent': 0}),
])
def test_summary_defaults_to_zero_when_tracking_is_absent(data, expected):
    assert tracking._summary(data) == expected
