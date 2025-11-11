import json
import os

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from flask import Blueprint

from ckanext.mwlr_datastore.logic import validators


def terms_of_use():
    return toolkit.render('terms_of_use.html')

class MwlrDatastorePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.ITemplateHelpers)

    def is_fallback(self):
        return True
    
    def package_types(self):
        return []

    def get_blueprint(self):
        """Provides Flask blueprint which sets up a custom
        `terms_of_use` URL. Uses IBlueprint interface."""
        blueprint = Blueprint('mwlr_datastore', self.__module__)
        rules = [('/terms_of_use','terms_of_use',terms_of_use),]
        for rule in rules:
            blueprint.add_url_rule(*rule)
        return blueprint


    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "mwlr_datastore")


    def get_validators(self):
        return validators.get_validators()

    def get_helpers(self):
        """Register template helper functions."""
        return {
            'get_env_var': self.get_env_var,
        }

    def get_env_var(self, var_name, default=None):
        """Get environment variable value with optional default.
        
        Args:
            var_name (str): Name of the environment variable
            default (str, optional): Default value if variable not found
            
        Returns:
            str: Environment variable value or default
        """
        return os.environ.get(var_name, default)

    def before_dataset_index(self, dataset_dict):
        '''
        Insert `vocab_author` into solr index with list of authors derived
        from the dataset_dict's `author` field.
        '''
        def listify_author(author_value):
            if isinstance(author_value, list):
                return author_value
            if author_value is None:
                return []
            try:
                return json.loads(author_value)
            except ValueError:
                return [author_value]

        author_value = listify_author(dataset_dict.get('author'))

        if dataset_dict.get('author'):
            dataset_dict['vocab_author'] = author_value

        ## Any 'repeating subfields' schema item must be converted to
        ## JSON strings before being indexed by Solr (currently only
        ## the 'custom' field).  This implementation is less general
        ## than the extension 'scheming_nerf_index but, is used here
        ## because it repeatedly states in the scheming documentation
        ## that this scheming_nerf_index is for testing only.
        if 'custom' in dataset_dict:
            dataset_dict['custom'] = json.dumps(dataset_dict['custom'])


        return dataset_dict

    ## IFacets

    def dataset_facets(self, facets_dict, package_type):
        _update_facets(facets_dict)
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        _update_facets(facets_dict)
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        _update_facets(facets_dict)
        return facets_dict

def _update_facets(facets_dict):

    facets_dict.update({
        'vocab_author': plugins.toolkit._('Authors')
    })




    
