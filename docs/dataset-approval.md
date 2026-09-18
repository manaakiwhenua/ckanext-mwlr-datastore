# Dataset approval

The `dataset_approval` plugin holds a dataset private until an admin of its organisation has reviewed and approved it. Editors submit for review; admins approve or reject with structured feedback; every decision is kept as a review history, and both sides are notified by email.

This page describes the workflow **as built** on CKAN 2.12, after the plugin moved into this extension ([MWDS-400](https://manaakiwhenua.atlassian.net/browse/MWDS-400)). It has not been through user testing since that move. Where the code and the intended behaviour may differ, it says so under [Open questions](#open-questions). For where the code came from and its licence, see the plugin's [README](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/blob/main/ckanext/datasetapproval/README.md).

How this plugin must fit with the others in this extension is set by [decision 0001](decisions/0001-plugin-composition.md).

## Turning it on

The plugin is off unless an environment lists it in `ckan.plugins`. Today only the approvals environment does, in the order `decision 0001` sets:

```text
mwlr_tracking tracking mwlr_datastore dataset_approval ... scheming_datasets ...
```

When it is listed, the DataStore image runs `ckan db upgrade -p dataset_approval` at start-up, creating its two tables. Environments that do not list it never get the tables.

| Setting | Does |
|---|---|
| `ckan.datastore.data_management_email` | the contact address shown on the review forms |
| `ckanext.approval.reviewer_guidelines_link` | a link to the reviewer guidelines, shown to reviewers |

## The workflow

A dataset's workflow state is its `publishing_status`:

| `publishing_status` | Means | Visibility |
|---|---|---|
| `in_progress` | an editor saved without submitting | forced private |
| `in_review` | an editor submitted it for review | private while in review |
| `approved` | an admin approved it, or an admin saved it | whatever the editor chose in `chosen_visibility` |
| `rejected` | an admin rejected it | forced private |

- **An organisation admin (or sysadmin) creating or editing** a dataset skips review: it goes straight to `approved` with the visibility they set.
- **An editor** either saves (`in_progress`, private) or submits for review (`in_review`). Submitting emails every admin of the organisation **and every sysadmin**.
- **An editor changing only visibility** on an approved dataset uses the "bypass review" button, which keeps it approved.
- **Reviewing:** admins see datasets awaiting them at `/user/<id>/dataset_review`; editors see their own submissions at `/user/<id>/my_requests`. The reviewer picks the review types that apply (metadata and documentation, scientific and technical, te ao Māori, ethics and security risk, intellectual property), then approves or rejects. Rejection takes one or more reasons and comments. The outcome is emailed to the dataset's editors.
- **History:** each approval or rejection is stored with its comments, and org admins and sysadmins can read it at `/dataset/review_history/<name>`.

## What it hooks into

| Extension point | What the plugin does |
|---|---|
| Chained actions | `package_create`, `package_update`, `resource_create`, `resource_update` run the publishing check before the save and send the review email after it; `package_show` is a pass-through |
| New actions | `workflow_actions_show`, `latest_workflow_action_show`, `retrieve_publishing_status`, `retrieve_rejection_reasons`, `check_user_admin` |
| Auth functions | `workflow_history_show` (org admin or sysadmin), `retrieve_publishing_status` (anyone) |
| `IPermissionLabels` | users flagged `has_approval_permission` see private datasets only in organisations they administer (see below) |
| `IPackageController` | `before_dataset_search` hides `in_progress`, `in_review` and `rejected` datasets from searches unless the user is a sysadmin or the search asks for drafts or reviews; `before_dataset_view` adds the latest workflow action to the dataset page |
| `IDatasetForm` | registered as the fallback form; inert while scheming owns the `dataset` type |
| Blueprints | its own `/dataset/new` and `/dataset/edit/<id>` views (to read the submit and bypass buttons), the review pages and the feedback endpoint |
| Templates | the dataset and resource forms' buttons and stages, the dataset page, search, the user dashboard tabs, `page.html` styles |
| Database | `workflow_action` and `review_comments` tables, with their own Alembic migrations |

## Data

The workflow state lives on the dataset itself, as fields that scheming has to declare: `publishing_status`, `chosen_visibility` and the review fields (`te_ao_māori_review_required`, `scientific_technical_review_required` and so on, with notes). Reviewer decisions and comments live in the plugin's own tables.

## Open questions

Found reading the code for [MWDS-469](https://manaakiwhenua.atlassian.net/browse/MWDS-469). Each needs confirming on the approvals environment before the workflow goes to testers.

1. **The workflow fields are not in the schema, so the workflow cannot run.** The fields above are commented out of `ckanext/mwlr_datastore/scheming/dataset.yaml` (MWDS-348 took them out so the workflow could be removed from production), and the approvals environment uses that same schema. CKAN's package schema drops undeclared top-level fields without an error, so `publishing_status` is thrown away on every save: nothing ever reaches `in_review`, the reviewer queue stays empty, and the approve and reject endpoints return 404 for every dataset. None of the approvals environment's public datasets has a `publishing_status`. Where these fields should live is an open question in [decision 0001](decisions/0001-plugin-composition.md#open-questions); something has to change before testing is worth anyone's time.
2. **Editing a resource may unpublish its dataset.** Adding or changing a resource calls `package_update` internally without the dataset form's context, so for an editor the publishing check takes the "saved, not submitted" branch: the dataset becomes private and `in_progress`. That may be intended (any change is reviewed again), but it happens silently and needs an explicit decision, especially once restricted resources lets an editor change a resource's access.
3. **`has_approval_permission` narrows what a user can see.** For a user with that flag in their `plugin_extras`, the plugin removes every organisation membership label and adds back only the organisations they administer, so they stop seeing private datasets in organisations where they are an editor or member. Nothing in the code sets the flag; it can only be set by hand. Decide whether the flag is still needed, and if so whether the narrowing is intended.
4. **`retrieve_publishing_status` answers anyone.** It reads the dataset with `ignore_auth` and its auth function allows anonymous access, so anyone who knows a dataset's id can learn whether it is in review or was rejected, including for private datasets. Low impact, but it should check `package_show` access first.
5. **The search filter is concatenated without a separator.** `before_dataset_search` prepends `!(publishing_status:(...))` directly to any existing `fq`, with no space or `AND`. With another filter present - a facet, or another plugin's filter - the combined query may not mean what it says. Access is not affected (CKAN applies permission labels separately), but in-review datasets could appear in listings for users who can already see them.
6. **Review requests go to every sysadmin**, as well as the organisation's admins. Confirm that is wanted at production volumes.
7. **An "approved for restricted access" outcome is waiting on restricted resources.** It is commented out of the approval outcomes "until restricted functionality implemented". That is the first concrete point where the two features meet, and belongs in the restricted resources design.
8. **The testing plan predates CKAN 2.12 and the move.** The [testing plan](https://manaakiwhenua.atlassian.net/wiki/spaces/CKAN/pages/16651878401) was last updated in December 2025 and needs revising once the points above are settled.
