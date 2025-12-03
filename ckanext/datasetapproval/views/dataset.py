# encoding: utf-8
import logging

from flask import Blueprint
from ckan.common import current_user
from ckan.lib.helpers import helper_functions as h
from ckan.plugins import toolkit as tk
import ckan.model as model
from ckan.views.dataset import (
    CreateView as BaseCreateView,
    EditView as BaseEditView,
    _get_package_type,
    _setup_template_variables,
    _get_pkg_template,
    _tag_string_to_list,
    _form_save_redirect,
)
from ckan.types import Context, Response

import ckan.lib.navl.dictization_functions as dict_fns
from ckan.lib.search import (
    SearchError, SearchQueryError, SearchIndexError
)
import ckan.logic as logic
from typing import Any, Iterable, Optional, Union, cast
from ckan.common import _, config, g, request

log = logging.getLogger(__name__)

dataset = Blueprint(
    "approval_dataset",
    __name__,
    url_prefix="/dataset",
    url_defaults={"package_type": "dataset"},
)
NotAuthorized = logic.NotAuthorized
check_access = logic.check_access

class CreateView(BaseCreateView):
    def __init__(self):
        super().__init__()
    
    def _prepare(self) -> Context:  # noqa
        log.debug("self in createview _prepare: %r", self)
        context = super()._prepare()
        context.update({'save_as_draft': tk.request.form.get("save") == "save-draft"})
        context.update({'admin_editing': h.is_admin(current_user.name)})
        return context

class EditView(BaseEditView):
    def __init__(self):
        super().__init__()
    
    def _prepare(self) -> Context:
        log.debug("self in editview _prepare: %r", self)
        context = super()._prepare()
        context.update({'save_as_draft': tk.request.form.get("save") == "save-draft"})
        context.update({'admin_editing': h.is_admin(current_user.name)})
        return context

dataset.add_url_rule("/new", view_func=CreateView.as_view(str("new")))
dataset.add_url_rule("/edit/<id>", view_func=EditView.as_view(str("edit")))

def registered_views():
    return dataset