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
            return base.abort(403, _(u'Unauthorized to create a package'))
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
    
    def get(self,
            package_type: str,
            id: str,
            data: Optional[dict[str, Any]] = None,
            errors: Optional[dict[str, Any]] = None,
            error_summary: Optional[dict[str, Any]] = None
            ) -> Union[Response, str]:
        context = self._prepare()
        package_type = _get_package_type(id) or package_type
        try:
            view_context = context.copy()
            view_context['for_view'] = True
            pkg_dict = tk.get_action(u'package_show')(
                view_context, {u'id': id})
            context[u'for_edit'] = True
            old_data = tk.get_action(u'package_show')(context, {u'id': id})
            # old data is from the database and data is passed from the
            # user if there is a validation error. Use users data if there.
            if data:
                old_data.update(data)
            data = old_data
        except (NotFound, NotAuthorized):
            return tk.base.abort(404, _(u'Dataset not found'))
        assert data is not None
        # are we doing a multiphase add?
        if data.get(u'state', u'').startswith(u'draft') and data.get('publishing_status') != 'in_review':
            tk.g.form_action = h.url_for(u'{}.new'.format(package_type))
            tk.g.form_style = u'new'

            return CreateView().get(
                package_type,
                data=data,
                errors=errors,
                error_summary=error_summary
            )

        pkg = context.get(u"package")
        resources_json = h.dump_json(data.get(u'resources', []))
        user = current_user.name
        try:
            check_access(
                'package_update',
                context,
                {"id": pkg_dict.get('id')}
            )
        except NotAuthorized:
            return tk.base.abort(
                403,
                _(u'User %r not authorized to edit %s') % (user, id)
            )
        # convert tags if not supplied in data
        if data and not data.get(u'tag_string'):
            data[u'tag_string'] = u', '.join(
                h.dict_list_reduce(pkg_dict.get(u'tags', {}), u'name')
            )
        errors = errors or {}
        form_snippet = _get_pkg_template(
            u'package_form', package_type=package_type
        )
        form_vars: dict[str, Any] = {
            u'data': data,
            u'errors': errors,
            u'error_summary': error_summary,
            u'action': u'edit',
            u'dataset_type': package_type,
            u'form_style': u'edit'
        }
        errors_json = h.dump_json(errors)

        # TODO: remove
        tk.g.pkg = pkg
        tk.g.resources_json = resources_json
        tk.g.errors_json = errors_json

        _setup_template_variables(
            context, {u'id': id}, package_type=package_type
        )

        # we have already completed stage 1
        form_vars[u'stage'] = [u'active']
        if data.get(u'state', u'').startswith(u'draft'):
            form_vars[u'stage'] = [u'active', u'complete']

        edit_template = _get_pkg_template(u'edit_template', package_type)
        return tk.base.render(
            edit_template,
            extra_vars={
                u'form_vars': form_vars,
                u'form_snippet': form_snippet,
                u'dataset_type': package_type,
                u'pkg_dict': pkg_dict,
                u'pkg': pkg,
                u'resources_json': resources_json,
                u'errors_json': errors_json
            }
        )

dataset.add_url_rule("/new", view_func=CreateView.as_view(str("new")))
dataset.add_url_rule("/edit/<id>", view_func=EditView.as_view(str("edit")))

def registered_views():
    return dataset