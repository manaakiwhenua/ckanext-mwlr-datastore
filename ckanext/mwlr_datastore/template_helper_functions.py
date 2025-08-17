## These functions are used by the plugin (probably in plugin.py) to
## generate cutom html template content.

import ckan.plugins.toolkit as toolkit

def get_package_tracking_total(package_id):
    '''Return package data for the given id, incuding trackign
    data.'''
    data = toolkit.get_action('package_show')(
        data_dict={
            'name_or_id':"package_id",
            'include_tracking':True,}
    )
    return data['tracking_summary']['total']

def get_package_tracking_recent(package_id):
    '''Return package data for the given id, incuding trackign
    data.'''
    data = toolkit.get_action('package_show')(
        data_dict={
            'name_or_id':"package_id",
            'include_tracking':True,}
    )
    return data['tracking_summary']['recent']
