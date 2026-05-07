# probably need to import a bunch of stuff that is needed
from typing import Any
import ckan.tests.helpers as test_helpers
import ckan.tests.factories as factories
import ckan.plugins.toolkit as tk

import logging
logger = logging.getLogger(__name__)
import pytest
pytestmark = pytest.mark.usefixtures("standard_plugins")
# what fixtures are needed?

# create an org

# have a user that is an admin of that org

# have a user that is an editor of that org

# have an already created, valid and approved dataset (belonging to that org)


# passing through a newly created dataset function, and the database
def test_editor_create_dataset(make_dataset, org_with_editor):
    # get the org and the user with editor capacity in that org
    organization, user = org_with_editor
    
    # create the dataset as an editor
    test_dataset = make_dataset(organization["id"], user)

    assert test_dataset["owner_org"] == organization["id"]
    assert test_dataset["publishing_status"] == "in_progress"



# passing through a newly created dataset function, and the database
def test_admin_create_dataset(make_dataset, org_with_admin):
    # get the org and the user with admin capacity in that org
    organization, user = org_with_admin
    
    # create the dataset as an admin
    test_dataset = make_dataset(organization["id"], user, admin_editing=True)

    assert test_dataset["owner_org"] == organization["id"]
    assert test_dataset["publishing_status"] == "approved"