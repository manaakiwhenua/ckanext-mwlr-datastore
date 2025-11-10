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
import ckan.logic as logic
from typing import Any, Iterable, Optional, Union, cast
from ckan.common import _

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
        context = cast(Context, {
            u'model': model,
            u'session': model.Session,
            u'user': current_user.name,
            u'auth_user_obj': current_user,
            u'save': self._is_save(),
            u'save_as_draft': tk.request.form.get("save") == "save-draft",
            u'admin_editing': h.is_admin(current_user.name),
        })
        try:
            check_access(u'package_create', context)
        except NotAuthorized:
            return tk.base.abort(403, _(u'Unauthorized to create a package'))
        return context

    def get(
        self,
        package_type,
        term_agree=False,
        data=None,
        errors=None,
        error_summary=None,
    ):

        if error_summary or errors or data:
            return super().get(package_type, data, errors, error_summary)
        return super().get(package_type)

class EditView(BaseEditView):
    def __init__(self):
        super().__init__()
    
    def _prepare(self) -> Context:
        log.debug("self in editview _prepare: %r", self)
        context: Context = {
            u'user': current_user.name,
            u'auth_user_obj': current_user,
            u'save': u'save' in tk.request.form,
            u'save_as_draft': tk.request.form.get("save") == "save-draft",
            u'admin_editing': h.is_admin(current_user.name)
        }
        return context

dataset.add_url_rule("/new", view_func=CreateView.as_view(str("new")))
dataset.add_url_rule("/edit/<id>", view_func=EditView.as_view(str("edit")))

def registered_views():
    return dataset