import json

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from flask import Blueprint

from ckanext.mwlr_datastore.logic import validators
from ckanext.mwlr_datastore.template_helper_functions import *


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

    ## ITemplateHelpers
    def get_helpers(self):
        '''Register custom template helper functions.'''
        return {
            'datastore_get_package_tracking_total': get_package_tracking_total,
            'datastore_get_package_tracking_recent': get_package_tracking_recent,
        }

def _update_facets(facets_dict):

    facets_dict.update({
        'vocab_author': plugins.toolkit._('Authors')
    })




    
