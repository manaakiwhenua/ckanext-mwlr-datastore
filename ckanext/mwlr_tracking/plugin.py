import hashlib
import re

import six
import sqlalchemy as sa

## use log.debug('...') or log.info('...') to print information
import logging
log = logging.getLogger(__name__)

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class MwlrTrackingPlugin(plugins.SingletonPlugin):

    """This plugin adds resource download tracking to CKAN and jinja2
    templates to show recent and total package and resource
    views/downloads in the UI.

    It builds on CKAN-2.10's built-in tracking capability and requires
    the configuration variable ckan.tracking_enabled=True. CKAN 2.11
    has moved tracking to a native extension and may work differently,
    hopefully negating the need for the resource tracking middleware
    included in this plugin."""
    
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
        logging.info('mwlr_tracking_middleware added')
        return MwlrTrackingMiddleware(app, config)

def get_package_tracking_total(package_id):
    '''Return tracking total for this package id.'''
    data = toolkit.get_action('package_show')(
        data_dict={
            'id':package_id,
            'include_tracking':True,}
    )
    return data['tracking_summary']['total']

def get_package_tracking_recent(package_id):
    '''Return tracking recent total for this package id.'''
    data = toolkit.get_action('package_show')(
        data_dict={
            'id':package_id,
            'include_tracking':True,}
    )
    return data['tracking_summary']['recent']

def get_resource_tracking_total(resource_id):
    '''Return tracking total for this resource id.'''
    data = toolkit.get_action('resource_show')(
        data_dict={
            'id':resource_id,
            'include_tracking':True,}
    )
    return data['tracking_summary']['total']

def get_resource_tracking_recent(resource_id):
    '''Return tracking recent total for this resource id.'''
    data = toolkit.get_action('resource_show')(
        data_dict={
            'id':resource_id,
            'include_tracking':True,}
    )
    return data['tracking_summary']['recent']



class MwlrTrackingMiddleware(object):

    """Alan Heays 2025-09-03: Define additional middleware to add
    resource downloads to the tracking_raw database.  These should be
    recorded by the internal CKAN tracking functionality but are not.
    Other kind of package links are successfully tracked without
    customisation. This code is based on the tracking.py in the CKAN
    source. Hopefully this can be removed in a future CKAN update."""
    
    def __init__(self, app, config):
        self.app = app
        self.engine = sa.create_engine(config.get('sqlalchemy.url'))
        self.config = config

    def __call__(self, environ, start_response):
        """The path points to a resource download add a line into the tracking_raw table. """
        ## this condition may fail in CKAN 2.11 where tracking has been
        ## moved from a configuration option to a native plugin
        if self.config.get('ckan.tracking_enabled'):
            path = environ['PATH_INFO']
            if re.match(r'/dataset/[0-9a-f-]+/resource/[0-9a-f-]+/download/.+', path):
                key = ''.join([
                    environ['HTTP_USER_AGENT'],
                    environ['REMOTE_ADDR'],
                    environ.get('HTTP_ACCEPT_LANGUAGE', ''),
                    environ.get('HTTP_ACCEPT_ENCODING', ''),
                ])
                key = hashlib.md5(six.ensure_binary(key)).hexdigest()
                sql = '''INSERT INTO tracking_raw
                             (user_key, url, tracking_type)
                             VALUES (%s, %s, %s)'''
                ## the extraction of resource tracking data by the
                ## resource_show action requires an exact match of the
                ## full url, so the site_url is prepended to the resource download path
                url = self.config.get('ckan.site_url', 'http://0.0.0.0')+path
                self.engine.execute(sql, key,url,'resource')
            return self.app(environ, start_response)
