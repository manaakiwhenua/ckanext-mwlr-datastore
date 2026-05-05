# encoding: utf-8
import logging

from flask import Blueprint
from ckan.common import current_user
from ckan.lib.helpers import helper_functions as h
from ckan.plugins import toolkit as tk
from ckan.views.dataset import (
    CreateView as BaseCreateView,
    EditView as BaseEditView,
)
from ckan.lib.search import (
    SearchIndexError
)
import ckan.lib.base as base
from ckan.types import Context
import ckan.logic as logic
from ckan.common import _, request

log = logging.getLogger(__name__)

dataset = Blueprint(
    "approval_dataset",
    __name__,
    url_prefix="/dataset",
    url_defaults={"package_type": "dataset"},
)

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError

class CreateView(BaseCreateView):
    def __init__(self):
        super().__init__()
    
    def _prepare(self) -> Context:  # noqa
        log.debug("dataset self in createview _prepare: %r", self)
        context = super()._prepare()
        selected_org = tk.request.form.get("owner_org")
        context.update({'submit_review': tk.request.form.get("save") == "submit-review"})
        context.update({'admin_editing': h.is_admin(current_user.name, selected_org)})
        return context

class EditView(BaseEditView):
    def __init__(self):
        super().__init__()
    
    def _prepare(self) -> Context:
        log.debug("dataset self in editview _prepare: %r", self)
        context = super()._prepare()
        selected_org = tk.request.form.get("owner_org")
        context.update({'submit_review': tk.request.form.get("save") == "submit-review"})
        context.update({'admin_editing': h.is_admin(current_user.name, selected_org)})
        return context

    def post(self, package_type, id):
        if tk.request.form.get("save") == "bypass-review":
            try:
                context = self._prepare()
                context.update({'bypass_review': True})
                pkg_dict = tk.get_action("package_patch")(
                    context,
                    {
                        "id": id,
                        "chosen_visibility": tk.request.form.get("chosen_visibility"),
                        "private": tk.request.form.get("private"),
                    },
                )
                tk.h.flash_success("Dataset visibility successfully updated")
                return tk.redirect_to(u'{}.read'.format(package_type),
                                id=pkg_dict['name'])
            except NotAuthorized:
                return base.abort(403, _(u'Unauthorized to read package %s') % id)
            except NotFound:
                return base.abort(404, _(u'Dataset not found'))
            except SearchIndexError as e:
                log.exception('SearchIndexError on package_patch')
                return base.abort(
                    500,
                    _(u'Unable to update search index.')
                )
            except ValidationError as e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.get(package_type, id, pkg_dict, errors, error_summary)


        return super().post(package_type, id)
    
dataset.add_url_rule("/new", view_func=CreateView.as_view(str("new")))
dataset.add_url_rule("/edit/<id>", view_func=EditView.as_view(str("edit")))

def registered_views():
    return dataset