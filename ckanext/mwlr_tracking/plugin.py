import json

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
### from flask import Blueprint


class MwlrTrackingPlugin(plugins.SingletonPlugin):


    ### plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigurer)
    ### plugins.implements(plugins.IValidators)
    ### plugins.implements(plugins.IPackageController, inherit=True)
    ### plugins.implements(plugins.IFacets)
    plugins.implements(plugins.ITemplateHelpers)    

    ## Template
    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")

    ## ITemplateHelpers
    def get_helpers(self):
        '''Register custom template helper functions.'''
        return {
            'datastore_get_package_tracking_total': get_package_tracking_total,
            'datastore_get_package_tracking_recent': get_package_tracking_recent,
        }


## custom template helper functions

def get_package_tracking_total(package_id):
    '''Return package data for the given id, incuding trackign
    data.'''
    data = toolkit.get_action('package_show')(
        data_dict={
            'name_or_id':package_id,
            'include_tracking':True,}
    )
    return data['tracking_summary']['total']

def get_package_tracking_recent(package_id):
    '''Return package data for the given id, incuding trackign
    data.'''
    data = toolkit.get_action('package_show')(
        data_dict={
            'name_or_id':package_id,
            'include_tracking':True,}
    )
    return data['tracking_summary']['recent']








