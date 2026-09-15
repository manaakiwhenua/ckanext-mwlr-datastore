"""Readiness: has this extension finished initialising? (MWDS-378)

The endpoint a readiness probe binds to. It answers one question - did the
parts of CKAN this extension depends on come up - from in-memory state only:

- the dataset schema is loaded by ckanext-scheming,
- this extension's template helpers are registered,
- a template renders through this extension's template directory.

It never calls the database or the search index. Readiness that fails on a
Solr or Postgres blip turns a dependency hiccup into an outage the probe
caused, and with a single replica there is nowhere else to send traffic.
Whether dependencies are reachable is monitoring's question, not this one's.

Configuration the deployment references (files, paths) is not checked here
either: that is a property of the deployment, not of the extension, and it is
a boot-time fact better checked once before the web server starts.
"""
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from flask import jsonify

DEFAULT_PATH = '/mwlr_datastore/ready'

REQUIRED_HELPERS = ('mwlr_versions', 'mwlr_environment', 'get_env_var')


def readiness_path():
    """Namespaced by default, so installing the extension does not claim a
    generic path like /healthz in someone else's URL space."""
    return toolkit.config.get('ckanext.mwlr_datastore.readiness_path') or DEFAULT_PATH


def _dataset_schema():
    if not plugins.plugin_loaded('scheming_datasets'):
        return 'scheming_datasets is not loaded'
    from ckanext.scheming.helpers import scheming_get_dataset_schema
    if not scheming_get_dataset_schema('dataset'):
        return "no schema loaded for dataset type 'dataset'"
    return None


def _template_helpers():
    missing = [name for name in REQUIRED_HELPERS if name not in toolkit.h]
    if missing:
        return 'helpers not registered: ' + ', '.join(missing)
    return None


def _template_renders():
    if toolkit.render('mwlr_datastore/readiness.html').strip() != 'ok':
        return 'readiness template did not render as expected'
    return None


CHECKS = (
    ('dataset_schema', _dataset_schema),
    ('template_helpers', _template_helpers),
    ('template_renders', _template_renders),
)


def run_checks():
    """{check name: None if it passed, else why it failed}."""
    results = {}
    for name, check in CHECKS:
        try:
            results[name] = check()
        except Exception as e:
            results[name] = '{}: {}'.format(type(e).__name__, e)
    return results


def ready():
    results = run_checks()
    is_ready = not any(results.values())
    response = jsonify({
        'ready': is_ready,
        'checks': {name: (failure or 'ok') for name, failure in results.items()},
    })
    response.status_code = 200 if is_ready else 503
    response.headers['Cache-Control'] = 'no-store'
    return response
