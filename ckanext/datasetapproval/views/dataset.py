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
            u'save': self._is_save()
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

        def post(self, package_type: str) -> Union[Response, str]:
            log.debug("In createview post method")
            # The staged add dataset used the new functionality when the dataset is
            # partially created so we need to know if we actually are updating or
            # this is a real new.
            context = self._prepare()
            is_an_update = False
            save_draft = tk.request.form.get("save") == "save-draft"
            log.debug("saved as draft: %r", save_draft)
            ckan_phase = request.form.get(u'_ckan_phase')
            try:
                data_dict = clean_dict(
                    dict_fns.unflatten(tuplize_dict(parse_params(request.form)))
                )
            except dict_fns.DataError:
                return base.abort(400, _(u'Integrity Error'))
            try:
                if ckan_phase:
                    # sort the tags
                    if u'tag_string' in data_dict:
                        data_dict[u'tags'] = _tag_string_to_list(
                            data_dict[u'tag_string']
                        )
                    if data_dict.get(u'pkg_name') or save_draft:
                        is_an_update = True
                        # This is actually an update not a save
                        data_dict[u'id'] = data_dict[u'pkg_name']
                        del data_dict[u'pkg_name']
                        # don't change the dataset state
                        data_dict[u'state'] = u'draft'
                        # this is actually an edit not a save
                        pkg_dict = get_action(u'package_update')(
                            context, data_dict
                        )

                        # redirect to add dataset resources
                        try:
                            last_added_resource = pkg_dict[u'resources'][-1]
                        except IndexError:
                            last_added_resource = None
                        if last_added_resource and request.form[u'save'] == "go-resources":
                            url = h.url_for(
                                u'{}_resource.edit'.format(package_type),
                                id=pkg_dict.get('id'),
                                resource_id=last_added_resource.get('id'))
                        elif request.form[u'save'] == "go-metadata-preview":
                            url = h.url_for(
                                u'{}.read'.format(package_type),
                                id=pkg_dict.get('id')
                            )
                        else:
                            url = h.url_for(
                                u'{}_resource.new'.format(package_type),
                                id=pkg_dict[u'name']
                            )
                        return h.redirect_to(url)
                    # Make sure we don't index this dataset
                    if request.form[u'save'] not in [
                        u'go-resource', u'go-metadata'
                    ]:
                        data_dict[u'state'] = u'draft'
                    # allow the state to be changed
                    context[u'allow_state_change'] = True

                data_dict[u'type'] = package_type
                pkg_dict = get_action(u'package_create')(context, data_dict)
                log.debug("testing pkg_dict from createview: %r", pkg_dict)

                create_on_ui_requires_resources = config.get(
                    'ckan.dataset.create_on_ui_requires_resources'
                )
                if ckan_phase:
                    if create_on_ui_requires_resources:
                        # redirect to add dataset resources if
                        # create_on_ui_requires_resources is set to true
                        url = h.url_for(
                            u'{}_resource.new'.format(package_type),
                            id=pkg_dict[u'name']
                        )
                        return h.redirect_to(url)
                    get_action(u'package_update')(
                        Context(context, allow_state_change=True),
                        dict(pkg_dict, state=u'active')
                    )
                    return h.redirect_to(
                        u'{}.read'.format(package_type),
                        id=pkg_dict["id"]
                    )

                return _form_save_redirect(
                    pkg_dict[u'name'], u'new', package_type=package_type
                )
            except NotAuthorized:
                return base.abort(403, _(u'Unauthorized to read package'))
            except NotFound:
                return base.abort(404, _(u'Dataset not found'))
            except SearchIndexError as e:
                try:
                    exc_str = str(repr(e.args))
                except Exception:  # We don't like bare excepts
                    exc_str = str(str(e))
                return base.abort(
                    500,
                    _(u'Unable to add package to search index.') + exc_str
                )
            except ValidationError as e:
                errors = e.error_dict
                error_summary = e.error_summary
                if is_an_update:
                    # we need to get the state of the dataset to show the stage we
                    # are on.
                    pkg_dict = get_action(u'package_show')(context, data_dict)
                    data_dict[u'state'] = pkg_dict[u'state']
                    return EditView().get(
                        package_type,
                        data_dict[u'id'],
                        data_dict,
                        errors,
                        error_summary
                    )
                data_dict[u'state'] = u'none'
                return self.get(package_type, data_dict, errors, error_summary)

class EditView(BaseEditView):
    def __init__(self):
        super().__init__()

    def get(self, package_type, id, data=None, errors=None, error_summary=None):
        context = self._prepare()
        package_type = _get_package_type(id) or package_type

        try:
            view_context = context.copy()
            view_context["for_view"] = True
            pkg_dict = tk.get_action("package_show")(view_context, {"id": id})
            context["for_edit"] = True
            old_data = tk.get_action("package_show")(context, {"id": id})

            if data:
                old_data.update(data)
            data = old_data
        except (tk.ObjectNotFound, tk.NotAuthorized):
            return tk.base.abort(404, tk._("Dataset not found"))

        assert data is not None

        pkg = context.get("package")
        resources_json = tk.h.dump_json(data.get("resources", []))
        user = current_user.name

        try:
            tk.check_access("package_update", context)
        except tk.NotAuthorized:
            return tk.base.abort(
                403, tk._("User %r not authorized to edit %s") % (user, id)
            )

        if data and not data.get("tag_string"):
            data["tag_string"] = ", ".join(
                tk.h.dict_list_reduce(pkg_dict.get("tags", {}), "name")
            )

        errors = errors or {}
        form_snippet = _get_pkg_template("package_form", package_type=package_type)
        form_vars = {
            "data": data,
            "errors": errors,
            "error_summary": error_summary,
            "action": "edit",
            "dataset_type": package_type,
            "form_style": "edit",
        }
        errors_json = tk.h.dump_json(errors)

        tk.g.pkg = pkg
        tk.g.resources_json = resources_json
        tk.g.errors_json = errors_json

        _setup_template_variables(context, {"id": id}, package_type=package_type)

        form_vars["stage"] = ["active"]
        if data.get("state", "").startswith("draft"):
            form_vars["stage"] = ["active", "complete"]

        edit_template = _get_pkg_template("edit_template", package_type)
        return tk.base.render(
            edit_template,
            extra_vars={
                "form_vars": form_vars,
                "form_snippet": form_snippet,
                "dataset_type": package_type,
                "pkg_dict": pkg_dict,
                "pkg": pkg,
                "resources_json": resources_json,
                "form_snippet": form_snippet,
                "errors_json": errors_json,
            },
        )

    def post(self, package_type, id):
        context = self._prepare()
        package_type = _get_package_type(id) or package_type
        log.debug("Package save request name: %s POST: %r", id, tk.request.form)
        save_draft = tk.request.form.get("save") == "save-draft"

        try:
            data_dict = logic.clean_dict(
                dict_fns.unflatten(
                    logic.tuplize_dict(logic.parse_params(tk.request.form))
                )
            )
        except dict_fns.DataError:
            return tk.abort(400, tk._("Integrity Error"))

        try:
            if "_ckan_phase" in data_dict:
                # we allow partial updates to not destroy existing resources
                context["allow_partial_update"] = True
                if "tag_string" in data_dict:
                    data_dict["tags"] = _tag_string_to_list(data_dict["tag_string"])
                del data_dict["_ckan_phase"]
                del data_dict["save"]
            data_dict["id"] = id
            if save_draft:
                data_dict["state"] = "draft"
            pkg_dict = tk.get_action("package_update")(context, data_dict)
            if save_draft:
                tk.h.flash_success(tk._("Dataset saved as draft"))
                return self.get(package_type, id, data=pkg_dict)
            else:
                return tk.redirect_to("approval_dataset.dataset_review", id=id)
        except tk.NotAuthorized:
            return tk.abort(403, tk._("Unauthorized to read package %s") % id)
        except tk.ObjectNotFound:
            return tk.abort(404, tk._("Dataset not found"))
        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(package_type, id, data_dict, errors, error_summary)


def dataset_review(package_type, id):
    # Retrieve the context for CKAN's logic functions
    context = {
        "model": model,
        "session": model.Session,
        "user": tk.c.user or tk.c.author,
    }
    try:
        package_dict = tk.get_action("package_show")(context, {"id": id})
    except tk.ObjectNotFound:
        tk.abort(404, tk._("Dataset not found"))
    except tk.NotAuthorized:
        tk.abort(401, tk._("Unauthorized to read dataset"))

    return tk.render(
        "package/snippets/review.html",
        extra_vars={"pkg_dict": package_dict, "data": package_dict},
    )


def dataset_publish(package_type, id):
    context = {
        "model": model,
        "session": model.Session,
        "user": tk.c.user or tk.c.author,
    }
    pkg_dict = tk.get_action("package_show")(context, {"id": id})
    resources = pkg_dict.get("resources", [])
    resources = sorted(resources, key=lambda x: x["created"], reverse=True)

    if tk.request.form["save"] == "go-resource":
        return tk.redirect_to(
            "resource.edit", id=pkg_dict["id"], resource_id=resources[0]["id"]
        )

    tk.get_action("package_patch")(context, {"id": id, "state": "active"})
    return tk.redirect_to("{}.read".format("dataset"), id=id)

dataset.add_url_rule("/new", view_func=CreateView.as_view(str("new")))
dataset.add_url_rule("/edit/<id>", view_func=EditView.as_view(str("edit")))
dataset.add_url_rule("/<id>/review", view_func=dataset_review)
dataset.add_url_rule("/<id>/publish", view_func=dataset_publish, methods=["POST"])


def registered_views():
    return dataset