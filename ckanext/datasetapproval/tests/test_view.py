# probably need to import a bunch of stuff that is needed
from typing import Any
import ckan.tests.helpers as test_helpers
import ckan.tests.factories as factories
import ckan.plugins.toolkit as tk

import logging
logger = logging.getLogger(__name__)
import pytest



@pytest.mark.usefixtures("standard_plugins")
def test_editor_saves_in_progress(app, make_dataset, org_with_editor):
    # create the org, editor and existing dataset
    organization, editor = org_with_editor
    dataset = make_dataset(
        organization["id"],
        editor,
    )
    form_data = dict(dataset)
    env = {"REMOTE_USER": editor["name"]}

    # save and submit the dataset as "in_progress"
    form_data["save"] = "" # as saving as "in_progress" so no value sent
    response = app.post(
        f"/dataset/edit/{form_data['name']}",
        data=form_data,
        environ_overrides=env,
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)

    updated_dataset = tk.get_action("package_show")(
        {"ignore_auth": True},
        {"id": form_data["id"]},
    )

    assert updated_dataset.get('publishing_status', None) == 'in_progress'
    assert updated_dataset.get('private', True) == True


@pytest.mark.usefixtures("standard_plugins")
def test_editor_submits_for_review(app, make_dataset, org_with_editor):
    # create the org, editor and existing dataset
    organization, editor = org_with_editor
    dataset = make_dataset(
        organization["id"],
        editor,
        private="true",
    )
    form_data = dict(dataset)
    env = {"REMOTE_USER": editor["name"]}

    # save and submit the dataset as "submit-review"
    form_data["save"] = "submit-review" 
    response = app.post(
        f"/dataset/edit/{form_data['name']}",
        data=form_data,
        environ_overrides=env,
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)

    updated_dataset = tk.get_action("package_show")(
        {"ignore_auth": True},
        {"id": dataset["id"]},
    )

    assert updated_dataset.get('publishing_status', None) == 'in_review'
    assert updated_dataset.get('private', True) == True


@pytest.mark.usefixtures("standard_plugins")
def test_editor_bypass_review(app, make_dataset, org_with_editor):
    # create the org, editor and existing dataset
    organization, editor = org_with_editor
    dataset = make_dataset(
        organization["id"],
        editor,
        publishing_status="approved",
    )
    form_data = dict(dataset)
    env = {"REMOTE_USER": editor["name"]}

    # save and submit the dataset as "bypass-review"
    form_data["save"] = "bypass-review" 
    response = app.post(
        f"/dataset/edit/{form_data['name']}",
        data=form_data,
        environ_overrides=env,
        follow_redirects=False,
    )


    assert response.status_code in (302, 303)

    updated_dataset = tk.get_action("package_show")(
        {"ignore_auth": True},
        {"id": form_data["id"]},
    )

    assert updated_dataset.get('publishing_status', None) == 'approved'
    assert updated_dataset["private"] == (
        updated_dataset["chosen_visibility"] == "true"
    )

@pytest.mark.usefixtures("standard_plugins")
def test_admin_update_approved_dataset(app, make_dataset, org_with_admin):
    # create the org, admin and existing approved dataset
    organization, admin = org_with_admin
    dataset = make_dataset(
        organization["id"],
        admin,
        admin_editing=True,
        publishing_status="approved",
    )
    form_data = dict(dataset)
    env = {"REMOTE_USER": admin["name"]}

    # admin should only send submit-review
    form_data["save"] = "submit-review" 
    admin_chosen_visibility = "false"
    form_data["private"] = admin_chosen_visibility # update the visibility as an admin
    response = app.post(
        f"/dataset/edit/{form_data['name']}",
        data=form_data,
        environ_overrides=env,
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)

    updated_dataset = tk.get_action("package_show")(
        {"ignore_auth": True},
        {"id": form_data["id"]},
    )

    assert updated_dataset.get('publishing_status', None) == 'approved'
    assert updated_dataset["private"] == (
        admin_chosen_visibility == "true"
    )