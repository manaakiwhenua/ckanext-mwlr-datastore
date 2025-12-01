import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultPermissionLabels
from ckan.authz import users_role_for_group_or_org
from ckanext.datasetapproval import views

from ckanext.datasetapproval import auth, actions, blueprints, helpers

import json
import logging as log
from ckan.common import _, c

log = log.getLogger(__name__)

import six
from six import text_type
def unicode_please(value):
    if isinstance(value, six.binary_type):
        try:
            return six.ensure_text(value)
        except UnicodeDecodeError:
            return value.decode(u'cp1252')
    return text_type(value)


def editor_publishing_dataset(owner_org, user_obj):
    '''
    Check if user is editor of the organization
    '''
    user_capacity = users_role_for_group_or_org(owner_org, user_obj.name)
    if user_obj.sysadmin:
        return False
    return user_capacity != 'admin'

class DatasetapprovalPlugin(plugins.SingletonPlugin, 
        DefaultPermissionLabels, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IPermissionLabels, inherit=True)



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
        }
        
    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'package_show_with_approval': auth.package_show_with_approval
        }

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        return True

    def package_types(self):
        # registers itself as the default (above).
        return []

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'is_admin': helpers.is_admin,
        }

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
                'fq': '!(publishing_status:(draft OR in_review OR rejected))' + search_params.get('fq', '')
            })
        return search_params

    @staticmethod
    def _publishing_status(package):
        # `package` is a model.Package object
        # with extras as model.PackageExtra rows
        log.debug("Getting publishing_status for package: %r", package.extras)
        for extra in package.extras:
            log.debug("Checking extra: %r", extra)
            if extra == 'publishing_status':
                log.debug("publishing_status extra found: %r",package.extras.get(extra))
                return package.extras.get(extra)
        return None

    def get_dataset_labels(self, dataset_obj):
        labels = super(DatasetapprovalPlugin, self) \
            .get_dataset_labels(dataset_obj)

        status = self._publishing_status(dataset_obj)

        if status == 'draft':
            # Remove ALL generic visibility labels
            cleaned = []
            for l in labels:
                # Drop public and all organisation membership labels
                if l == 'public':
                    continue
                if l.startswith('member-'):
                    continue
                cleaned.append(l)
            labels = cleaned

            # Add a label that only the creator user will have
            if dataset_obj.creator_user_id:
                labels.append(u'draft-owner-{0}'.format(
                    dataset_obj.creator_user_id))

        return labels

    # --- user labels (what labels a user is allowed to see) ---
    def get_user_dataset_labels(self, user_obj):
        # Start with the normal labels a user already has
        labels = super(DatasetapprovalPlugin, self) \
            .get_user_dataset_labels(user_obj)

        # Give each user a label matching “their” drafts
        labels.append(u'draft-owner-{0}'.format(user_obj.id))

        if user_obj and hasattr(user_obj, 'plugin_extras') and user_obj.plugin_extras:
            if user_obj.plugin_extras.get('has_approval_permission', False):
                labels = [x for x in labels if not x.startswith('member')]
                orgs = toolkit.get_action(u'organization_list_for_user')(
                    {u'user': user_obj.id}, {u'permission': u'admin'})
                labels.extend(u'member-%s' % o['id'] for o in orgs)
        return labels

    # IBlueprint
    def get_blueprint(self):
        full_blueprints = [views.dataset.registered_views(), blueprints.approveBlueprint]
        return full_blueprints


