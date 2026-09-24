import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.bsi_restricted_resources import actions, auth
from ckanext.bsi_restricted_resources.logic import access_helpers
import logging as log

log = log.getLogger(__name__)

class BsiRestrictedResourcesPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)

    def get_helpers(self):
        return access_helpers.get_access_helpers()
    
    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

    def get_actions(self):
        return actions.get_actions()

    def get_auth_functions(self):
        return auth.get_auth_functions()