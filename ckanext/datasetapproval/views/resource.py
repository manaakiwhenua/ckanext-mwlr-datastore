# encoding: utf-8
import logging
import cgi

from ckan.types import Response
from flask import Blueprint
from ckan.common import current_user
from ckan.plugins import toolkit as tk
from ckan.views.resource import CreateView as BaseCreateView, EditView as BaseEditView
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
from ckan import model
from ckan.types import Context
import ckan.lib.helpers as h

log = logging.getLogger(__name__)

resource = Blueprint(
    "approval_dataset_resource",
    __name__,
    url_prefix="/dataset/<id>/resource",
    url_defaults={"package_type": "dataset"},
)

prefixed_resource = Blueprint(
    "approval_resource",
    __name__,
    url_prefix="/dataset/<id>/resource",
    url_defaults={"package_type": "dataset"},
)


class CreateView(BaseCreateView):
    def __init__(self):
        super().__init__()
    
    def _prepare(self) -> Context:  # noqa
        log.debug("resource self in createview _prepare: %r", self)
        context = super()._prepare()
        context.update({'submit_review': tk.request.form.get("submit_review") == "submit"})
        context.update({'admin_editing': h.is_admin(current_user.name)})
        return context

    def post(self, package_type, id):
        return super().post(package_type, id)

class EditView(BaseEditView):
    def __init__(self):
        super().__init__()
    
    def _prepare(self) -> Context:  # noqa
        log.debug("resource self in editview _prepare: %r", self)
        context = super()._prepare()
        context.update({'submit_review': tk.request.form.get("submit_review") == "submit"})
        context.update({'admin_editing': h.is_admin(current_user.name)})
        return context

    def post(self, package_type, id, resource_id):
        return super().post(package_type, id, resource_id)


def register_dataset_plugin_rules(blueprint):
    blueprint.add_url_rule("/new", view_func=CreateView.as_view(str("new")))
    blueprint.add_url_rule(
        "/<resource_id>/edit", view_func=EditView.as_view(str("edit"))
    )


register_dataset_plugin_rules(resource)
register_dataset_plugin_rules(prefixed_resource)


def registered_views():
    return resource, prefixed_resource