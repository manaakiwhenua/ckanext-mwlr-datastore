# 0001 - Plugin composition

**Status:** Proposed · **Date:** 2026-09-18 · **Jira:** [MWDS-469](https://manaakiwhenua.atlassian.net/browse/MWDS-469)

Proposed until the restricted resources design settles; the rules below are written so dataset approval can be tested against them now.

## Context

This extension ships CKAN plugins from one package: `mwlr_datastore` and, since v1.3.0, `dataset_approval`. Restricted resources ([User Requirements - DataStore Resource Access Control](https://manaakiwhenua.atlassian.net/wiki/spaces/CKAN/pages/17277124610)) is arriving as a third plugin here, `bsi_restricted_resources`, scaffolded in [MWDS-459](https://manaakiwhenua.atlassian.net/browse/MWDS-459).

Keeping them as separate plugins in one package is deliberate: one release train and one test suite, but each capability switched on per deployment by listing it in `ckan.plugins`. A plugin that is not listed does nothing, and `dataset_approval`'s database migrations only matter where it is listed.

Separate plugins still share CKAN's extension points with each other and with CKAN's own plugins, and dataset approval and restricted resources both change **who can see what**. Some of those extension points combine plugins in order, and one of them silently ignores all but the first plugin. Without agreed rules, the second of the two to be written can quietly undo the first.

### How CKAN combines plugins

Checked against the CKAN 2.12.0 source. Two plugins overriding the same template file is not a problem in itself; it matters only when they replace the same **block**.

| Extension point | How several plugins combine | Source |
|---|---|---|
| Template overrides | The plugin listed **first** in `ckan.plugins` is searched first. With `{% ckan_extends %}` each override extends the next plugin's copy, so overrides of different blocks all apply. | `IConfigurer` iterates in reverse and `add_template_directory` prepends (`ckan/plugins/interfaces.py`, `ckan/plugins/toolkit.py`) |
| Chained actions (`@chained_action`) | Every plugin's function wraps the next; the plugin listed **first** is the **outermost** wrapper and sees the final result. | `get_action` in `ckan/logic/__init__.py` |
| Plain (unchained) action overrides | Two plugins overriding the same action raise `NameConflict` at startup. | same |
| `IPackageController` hooks | Run in list order; each sees the previous plugin's output. | `PluginImplementations` in `ckan/plugins/core.py` |
| Template helpers | Same name in two plugins: the plugin listed **first** wins, silently. | `ITemplateHelpers` iterates in reverse |
| **`IPermissionLabels`** | **Only the first plugin implementing it is used. Any other is ignored without an error.** | `get_permission_labels` in `ckan/lib/plugins.py` |

Permission labels are also **dataset-level only**: CKAN stores them on the dataset in the search index and filters searches and `package_show` by them. They cannot express "this resource is restricted but its dataset is not".

### Where the plugins overlap today

- **Permission labels:** `dataset_approval` implements `IPermissionLabels`; nothing else does. `bsi_restricted_resources` is a scaffold so far, with no actions, auth functions or labels yet.
- **Chained actions:** `dataset_approval` chains `package_create`, `package_update`, `package_show` (a pass-through), `resource_create` and `resource_update`.
- **Templates, between our plugins:** `package/read_base.html`, `package/search.html`, `page.html` and `scheming/package/snippets/resource_form.html` are overridden by both `mwlr_datastore` and `dataset_approval`, each on different blocks, so their order does not change what renders. `bsi_restricted_resources` overrides only `package/snippets/resource_item.html`, which neither of the others touches.
- **Templates, `mwlr_datastore` with core `tracking`:** both override `package/search.html` and `page.html`, on different blocks.
- **Templates, with core `tracking`:** CKAN's own `tracking` plugin (2.11 onwards) and `dataset_approval` both replace the same block in two templates, and neither calls `super()`:
    - `package/search.html`, block `form`: whichever is listed first supplies the search form. With `tracking` listed first, the sysadmin-only sort options `dataset_approval` adds (In progress, Rejected, Review pending) do not appear.
    - `snippets/package_item.html`, block `heading_meta`: `dataset_approval`'s version replaces the base and already includes the "recent views" badge. `tracking`'s version calls `super()` and adds the badge again, so with `tracking` first a popular dataset shows it twice.
- **Helpers:** no name collisions.
- **Plugin order is not written down anywhere:** this repository's CI lists `tracking` before `dataset_approval`.

## Decision

1. **Two ordering rules for `ckan.plugins`; everything else is free:**
    - restricted resources before `dataset_approval`, so its chained actions are the outermost: nothing another plugin does to a dataset or resource reaches a user without passing its check last;
    - `dataset_approval` before core `tracking`, so the workflow's search form and listing badges are the ones that render.

    `mwlr_datastore` shares no block, action or helper with either, so where it goes does not matter. A deployment that does not enable a plugin leaves it out, and the rules still hold for the rest. One order that meets them:

    ```text
    bsi_restricted_resources dataset_approval tracking mwlr_datastore ... scheming_datasets ...
    ```

2. **Exactly one `IPermissionLabels` implementation among our plugins.** Today that is `dataset_approval`. Restricted resources does not implement `IPermissionLabels`: labels cannot express resource-level restriction anyway. If a later feature needs dataset-level labels as well, the label logic moves into one implementation that combines the rules, rather than a second plugin implementing the interface.

3. **Resource-level access control uses chained auth functions and chained actions**, not permission labels: `resource_show`, `resource_view_show` and `resource_view_list` auth, the resource download route, and whatever `package_show` must hide from the resource list. This is also the approach of the main community extension, [ckanext-restricted](https://github.com/EnviDat/ckanext-restricted), although it replaces `package_show` and `resource_view_list` outright rather than chaining them, so it could not be adopted unmodified under rule 4.

4. **Every override of a core action or auth function is chained** (`@toolkit.chained_action`, `@toolkit.chained_auth_function`), never a plain replacement. Two plain replacements of the same action fail at startup, and a plain replacement discards core's implementation, so it has to reimplement it and keep up with every CKAN upgrade that changes it.

5. **Template overrides use `{% ckan_extends %}` and the narrowest block available, and call `super()` where they add to a block rather than replace it.** Two plugins replacing the same block is a bug to fix, not a precedence to rely on - including when the other plugin is one of CKAN's own. Where replacing is unavoidable, as with `dataset_approval`'s search form, rule 1 decides which one renders and the replacing template carries what the other one would have added.

6. **The test suite runs the plugins together, in an order that meets rule 1, and tests what they do together.**

## Alternatives considered

**Merge everything into `mwlr_datastore`.** One plugin removes ordering from the picture entirely. Rejected: switching the approval workflow off would need a feature flag of our own, where listing the plugin already does that for free, and the approval code, which carries Datopian's history and AGPL attribution, would lose its clear boundary. The composition problems do not go away either; they move inside one class where they are harder to see.

**No ordering rules, each plugin defensive about the others.** Rejected: permission labels cannot be made defensive - the ignored plugin never runs - and chained actions give different results in a different order by design.

**Restricted resources as a separate package.** Possible, and nothing here prevents it later. Rejected for now for the same reason approval moved into this extension ([MWDS-400](https://manaakiwhenua.atlassian.net/browse/MWDS-400)): one release train and one place for the tests that exercise the combination.

## Consequences

- Restricted resources has its integration points set before its design starts: chained auth functions and actions, no permission labels, listed before `dataset_approval`.
- A deployment's plugin list is checked against two rules rather than copied from one canonical list, so deployments that enable different plugins do not drift from each other.
- `dataset_approval` keeps replacing two blocks that core `tracking` also replaces (the search form and the listing badge), so its templates have to carry what `tracking` would have added, and keep doing so across CKAN upgrades.
- Adding a plugin, an action or auth override, or a template override that another plugin also touches means checking it against these rules in the same pull request.
- `dataset_approval` was checked against these rules before testing; what that found is on the [dataset approval](../dataset-approval.md#open-questions) page.

The work these lead to is tracked in Jira: [MWDS-537](https://manaakiwhenua.atlassian.net/browse/MWDS-537) (CI's plugin order), [MWDS-538](https://manaakiwhenua.atlassian.net/browse/MWDS-538) (tests of the plugins working together) and [MWDS-475](https://manaakiwhenua.atlassian.net/browse/MWDS-475) (the approval templates alongside core `tracking`).

## Open questions

- **Where a plugin's fields live.** The aim is that switching a plugin off hides its fields and switching it back on restores them. Constraints any answer has to meet:
    - scheming holds one schema per dataset type; a second file for the same type replaces the first, and there is no include or merge;
    - CKAN drops fields the schema does not declare, without an error, so removing a field from the schema loses its stored values the next time each dataset is edited;
    - some of these fields may describe the dataset rather than the workflow (whether a dataset needs te ao Māori review, for instance), and those may be worth keeping whether the workflow runs or not. That is for the data owners to say.

    **The current approach**, from [#48](https://github.com/manaakiwhenua/ckanext-mwlr-datastore/pull/48) ([MWDS-459](https://manaakiwhenua.atlassian.net/browse/MWDS-459)), is one schema per combination of plugins, and a deployment points `scheming.dataset_schemas` at the one that matches the plugins it lists:

    | Schema | For |
    |---|---|
    | `dataset.yaml` | neither plugin; the approval fields stay commented out ([MWDS-348](https://manaakiwhenua.atlassian.net/browse/MWDS-348)) |
    | `dataset_with_dataset_approval.yaml` | `dataset_approval` |
    | `dataset_with_restricted_resources.yaml` | restricted resources |
    | `dataset_with_both_restricted_resources_and_dataset_approval.yaml` | both |

    It meets the first constraint, since each deployment has exactly one schema. What it costs:
    - every field the files share is copied into each of them, and has to be kept in step by hand;
    - each plugin that adds fields doubles the number of files;
    - switching a plugin off still means moving to a schema without its fields, so their values are dropped on each dataset's next edit (the second constraint).

    To be confirmed by the approval workflow's maintainers (Mary O'Leary, Justine Waterson) as the intended answer. Restricted resources faces the same question for its resource fields, so once confirmed the answer becomes a rule here.
- **Blueprint precedence.** `dataset_approval` registers its own `/dataset/new` and `/dataset/edit/<id>` views, which scheming and core also register. Which one serves the request depends on registration order, not on this ADR's plugin order alone. Confirm on a deployment that lists `dataset_approval` and record the answer here.

## Revisit if

The restricted resources design needs dataset-level labels, a plugin moves out to its own package, or a CKAN upgrade changes how any extension point in the table above combines plugins.
