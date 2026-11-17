import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.bsi_restricted_resources import actions, auth
from ckanext.bsi_restricted_resources.logic import access_helpers, activity_helpers
import logging as log

log = log.getLogger(__name__)


class BsiRestrictedResourcesPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IResourceController, inherit=True)

    def get_helpers(self):
        return {
            **access_helpers.get_access_helpers(),
            **activity_helpers.get_helpers()
        }

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_resource("assets", "bsi_restricted_resources")

    def get_actions(self):
        return actions.get_actions()

    def get_auth_functions(self):
        return auth.get_auth_functions()

    def after_resource_create(self, context, resource):
        toolkit.get_action("restricted_resource_access_create")(context, resource)

    def after_resource_update(self, context, resource):
        toolkit.get_action("restricted_resource_access_update")(context, resource)

    def before_resource_delete(self, context, resource, resources):
        # We want to update the restricted resources table AFTER the resource has been deleted,
        # but, the after_resource_delete hook doesn't receive the resource id, so here, we
        # store it in context
        context["__restricted_resource_access_delete"] = resource["id"]

    def after_resource_delete(self, context, resources):
        # Use the id stored in the before_resource_delete hook
        toolkit.get_action("restricted_resource_access_delete")(context, { "id": context["__restricted_resource_access_delete"] })
