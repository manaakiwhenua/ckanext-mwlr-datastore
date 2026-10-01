# ckanext-mwlr-datastore

The CKAN extension behind [DataStore](https://datastore.landcareresearch.co.nz), the research data catalogue. The [README](https://github.com/manaakiwhenua/ckanext-mwlr-datastore#readme) covers installing, configuring, developing and releasing it; these pages cover how it works and why.

The DataStore deployment itself - the image, the environments, the pipeline - is documented with the DataStore component, not here.

## Plugins

One package, more than one CKAN plugin. Each is switched on by listing it in `ckan.plugins`, so an environment gets exactly the capabilities it lists.

| Plugin | What it does | Enabled |
|---|---|---|
| `mwlr_datastore` | the dataset schema and its validators, the theme templates, facets, view and download counts, environment and build helpers, the readiness endpoint | every environment |
| `dataset_approval` | the [dataset approval](dataset-approval.md) workflow | the approvals environment only |

Restricted resources is being designed ([User Requirements - DataStore Resource Access Control](https://manaakiwhenua.atlassian.net/wiki/spaces/CKAN/pages/17277124610)) and is expected to arrive as another plugin here.

## Plugin composition

Several of CKAN's extension points combine plugins - ours and CKAN's own - in the order they appear in `ckan.plugins`, and one - permission labels - uses only the first plugin that implements it. Dataset approval and restricted resources both change who can see what, so the order and the division of responsibilities are fixed in [decision 0001](decisions/0001-plugin-composition.md). In short:

- one order everywhere - `mwlr_datastore <restricted resources> dataset_approval tracking ...` - so access control wraps the workflow, and the workflow's templates win over core tracking's;
- exactly one of our plugins implements `IPermissionLabels`;
- resource-level access control uses chained auth functions and actions, not permission labels;
- every override of a core action or auth function is chained;
- the test suite runs the plugins together in that order.

Read the decision before adding a plugin, an action or auth override, or a template override that another plugin also touches.

## Decisions

Component decisions for this extension are in [Decisions](decisions/index.md).
