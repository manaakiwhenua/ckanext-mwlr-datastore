import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultPermissionLabels
from ckanext.datasetapproval import actions, blueprints, helpers, views, workflow_action_helpers, auth
import logging as log
from ckan.common import _, c

log = log.getLogger(__name__)

class DatasetapprovalPlugin(plugins.SingletonPlugin, 
        DefaultPermissionLabels, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IPermissionLabels, inherit=True)
    plugins.implements(plugins.IAuthFunctions)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets',
            'datasetapproval')

   # IActions
    def get_actions(self):
        return {
            'package_create': actions.package_create,
            'package_show': actions.package_show,
            'package_update': actions.package_update,
            'resource_create': actions.resource_create,
            'resource_update': actions.resource_update,
            'check_user_admin': actions.check_user_admin,
            'retrieve_rejection_reasons': actions.retrieve_rejection_reasons,
            'workflow_actions_show': actions.workflow_actions_show,
            'latest_workflow_action_show': actions.latest_workflow_action_show,
            'retrieve_publishing_status': actions.retrieve_publishing_status
        }

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        return True

    def package_types(self):
        # registers itself as the default (above).
        return []

    # ITemplateHelpers
    def get_helpers(self):
        helper_functions = {}

        helper_functions.update(helpers.get_helpers())
        helper_functions.update(workflow_action_helpers.get_helpers())
        return helper_functions

    def before_search(self, search_params):
        include_in_review = search_params.get('include_in_review', False)

        if include_in_review:
            search_params.pop('include_in_review', None)

        include_drafts = search_params.get('include_drafts', False)

        if toolkit.c.userobj:
            user_is_syadmin = toolkit.c.userobj.sysadmin
        else:
            user_is_syadmin = False
            
        if user_is_syadmin:
            return search_params
        elif include_in_review:
            return search_params
        elif include_drafts:
            return search_params
        else:   
            search_params.update({
                'fq': '!(publishing_status:(in_progress OR in_review OR rejected))' + search_params.get('fq', '')
            })
        return search_params

    #IPermissionLabels
    def get_user_dataset_labels(self, user_obj):
        labels = super(DatasetapprovalPlugin, self) \
            .get_user_dataset_labels(user_obj)

        if user_obj and hasattr(user_obj, 'plugin_extras') and user_obj.plugin_extras:
            if user_obj.plugin_extras.get('has_approval_permission', False):
                labels = [x for x in labels if not x.startswith('member')]
                orgs = toolkit.get_action(u'organization_list_for_user')(
                    {u'user': user_obj.id}, {u'permission': u'admin'})
                labels.extend(u'member-%s' % o['id'] for o in orgs)
        return labels


    # IBlueprint
    def get_blueprint(self):
        full_blueprints = [views.dataset.registered_views(),  blueprints.approveBlueprint]
        return full_blueprints

    # IPackageController
    def before_dataset_view(self, pkg_dict):
        '''
        This method is called before rendering the read.html page.
        You can add extra variables to the pkg_dict here which can then be accessed in the read.html template.
        '''
        try:
            endpoint = toolkit.request.endpoint
        except RuntimeError:
            return pkg_dict

        # Add latest workflow action details and additional reviews requested to the dataset read page. No permissions or workflow action comments are required.
        if endpoint and endpoint.endswith('dataset.read'):
            latest_workflow_action = toolkit.get_action('latest_workflow_action_show')(
                {},
                {'id': pkg_dict['id']}
            )
            pkg_dict['latest_workflow_action'] = latest_workflow_action
            pkg_dict['additional_reviews_requested'] = helpers.get_review_types_for_display(pkg_dict)
        return pkg_dict
        
    # IAuthFunctions
    def get_auth_functions(self):
        return auth.get_auth_functions()
