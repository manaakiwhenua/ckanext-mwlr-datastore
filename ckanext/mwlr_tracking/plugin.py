import hashlib
import re

import logging

import sqlalchemy as sa

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)


class MwlrTrackingPlugin(plugins.SingletonPlugin):

    """This plugin adds resource download tracking to CKAN and jinja2
    templates to show recent and total package and resource
    views/downloads in the UI.

    It builds on CKAN's page tracking. On CKAN 2.10 that is switched on
    with ckan.tracking_enabled = true; from CKAN 2.11 tracking lives in
    the core ``tracking`` plugin, which must be in ckan.plugins as well
    (list it after this plugin so these templates keep precedence).
    Core tracking counts page views only, on every CKAN so far, so the
    download middleware here is still needed on 2.11 and 2.12."""

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IMiddleware, inherit=True)

    def update_config(self, config_):
        """Point to overriding jinja2 templates."""
        toolkit.add_template_directory(config_, "templates")

    def get_helpers(self):
        """Register custom template helper functions used in custom
        jinja2 templates."""
        return {
            'datastore_get_package_tracking_total': get_package_tracking_total,
            'datastore_get_package_tracking_recent': get_package_tracking_recent,
            'datastore_get_resource_tracking_total': get_resource_tracking_total,
            'datastore_get_resource_tracking_recent': get_resource_tracking_recent,
        }

    def make_middleware(self, app, config):
        """Activate custom tracking middleware to get resource
        downloads tracked."""
        log.info('mwlr_tracking_middleware added')
        return MwlrTrackingMiddleware(app, config)


def tracking_active(config):
    """Whether CKAN is recording page views at all.

    CKAN 2.10 reads ckan.tracking_enabled. CKAN 2.11 moved tracking into
    the core ``tracking`` plugin and ignores the setting, so honour either.
    """
    if toolkit.asbool(config.get('ckan.tracking_enabled', False)):
        return True
    return plugins.plugin_loaded('tracking')


def _summary(data):
    """The tracking summary of a package or resource dict, or zeros.

    The key is only present when tracking is on (and, from CKAN 2.11,
    only when the core tracking plugin is loaded). A missing counter
    should render as 0, not take the page down.
    """
    summary = data.get('tracking_summary') or {}
    return {
        'total': summary.get('total', 0) or 0,
        'recent': summary.get('recent', 0) or 0,
    }


def _package_summary(package_id):
    data = toolkit.get_action('package_show')(
        data_dict={'id': package_id, 'include_tracking': True})
    return _summary(data)


def _resource_summary(resource_id):
    data = toolkit.get_action('resource_show')(
        data_dict={'id': resource_id, 'include_tracking': True})
    return _summary(data)


def get_package_tracking_total(package_id):
    '''Return tracking total for this package id.'''
    return _package_summary(package_id)['total']


def get_package_tracking_recent(package_id):
    '''Return tracking recent total for this package id.'''
    return _package_summary(package_id)['recent']


def get_resource_tracking_total(resource_id):
    '''Return tracking total for this resource id.'''
    return _resource_summary(resource_id)['total']


def get_resource_tracking_recent(resource_id):
    '''Return tracking recent total for this resource id.'''
    return _resource_summary(resource_id)['recent']


DOWNLOAD_PATH = re.compile(r'/dataset/[0-9a-f-]+/resource/[0-9a-f-]+/download/.+')

INSERT_TRACKING = sa.text('''INSERT INTO tracking_raw
                                 (user_key, url, tracking_type)
                             VALUES (:user_key, :url, :tracking_type)''')


def visitor_key(environ):
    """The same anonymous visitor hash CKAN's own tracking uses."""
    key = ''.join([
        environ.get('HTTP_USER_AGENT', ''),
        environ.get('REMOTE_ADDR', ''),
        environ.get('HTTP_ACCEPT_LANGUAGE', ''),
        environ.get('HTTP_ACCEPT_ENCODING', ''),
    ])
    return hashlib.md5(key.encode('utf-8')).hexdigest()


class MwlrTrackingMiddleware(object):

    """Alan Heays 2025-09-03: Define additional middleware to add
    resource downloads to the tracking_raw database.  These should be
    recorded by the internal CKAN tracking functionality but are not.
    Other kind of package links are successfully tracked without
    customisation. This code is based on the tracking.py in the CKAN
    source. Hopefully this can be removed in a future CKAN update.

    Still needed on CKAN 2.12: the core tracking plugin records page
    views posted to /_tracking and nothing else.
    """

    def __init__(self, app, config):
        self.app = app
        self.engine = sa.create_engine(config.get('sqlalchemy.url'))
        self.config = config

    def __getattr__(self, name):
        # Later IMiddleware plugins are handed this object, not the Flask
        # app, and core tracking (CKAN 2.11+) calls app.after_request on
        # it. Delegate anything that is not ours to the wrapped app.
        if name == 'app':
            raise AttributeError(name)
        return getattr(self.app, name)

    def __call__(self, environ, start_response):
        """The path points to a resource download add a line into the tracking_raw table. """
        if tracking_active(self.config):
            path = environ.get('PATH_INFO', '')
            if DOWNLOAD_PATH.match(path):
                self.record_download(visitor_key(environ), path)
        return self.app(environ, start_response)

    def record_download(self, user_key, path):
        ## the extraction of resource tracking data by the
        ## resource_show action requires an exact match of the
        ## full url, so the site_url is prepended to the resource download path
        url = self.config.get('ckan.site_url', 'http://0.0.0.0') + path
        # engine.begin() + text() is the SQLAlchemy 2 way and works on 1.4;
        # engine.execute(str, *args) is gone in 2.0 (CKAN 2.12).
        with self.engine.begin() as conn:
            conn.execute(INSERT_TRACKING, {
                'user_key': user_key, 'url': url, 'tracking_type': 'resource'})
