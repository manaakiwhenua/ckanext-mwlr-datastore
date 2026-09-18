"""View and download counts for the dataset and resource pages.

CKAN's own tracking collects the numbers: on 2.10 with
ckan.tracking_enabled = true, from 2.11 through the core ``tracking``
plugin. These helpers only read them for the two templates that show them
(package/snippets/info.html and scheming/package/resource_read.html). The
package and resource dicts some pages render with were built without
include_tracking, so the helpers ask for the summary themselves.
"""
import ckan.plugins.toolkit as toolkit


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


def get_helpers():
    return {
        'datastore_get_package_tracking_total': get_package_tracking_total,
        'datastore_get_package_tracking_recent': get_package_tracking_recent,
        'datastore_get_resource_tracking_total': get_resource_tracking_total,
        'datastore_get_resource_tracking_recent': get_resource_tracking_recent,
    }
