# 0001 - Plugin composition

**Status:** Proposed · **Date:** 2026-09-18 · **Jira:** [MWDS-469](https://manaakiwhenua.atlassian.net/browse/MWDS-469)

Proposed until the restricted resources design settles; the rules below are written so dataset approval can be tested against them now.

## Context

This extension ships CKAN plugins from one package: `mwlr_datastore` and, since v1.3.0, `dataset_approval`. A restricted resources feature is being planned ([User Requirements - DataStore Resource Access Control](https://manaakiwhenua.atlassian.net/wiki/spaces/CKAN/pages/17277124610)) and will most likely arrive as another plugin here.

Keeping them as separate plugins in one package is deliberate: one release train and one test suite, but each capability switched on per environment by listing it in `ckan.plugins`. `dataset_approval` is off everywhere except the approvals environment, and its database migration only runs when it is listed.

Separate plugins still share CKAN's extension points with each other and with CKAN's own plugins, and dataset approval and restricted resources both change **who can see what**. Some of those extension points combine plugins in order, and one of them silently ignores all but the first plugin. Without agreed rules, the second of the two to be written can quietly undo the first.

### How CKAN combines plugins

Checked against the CKAN 2.12.0 source.

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

- **Permission labels:** `dataset_approval` implements `IPermissionLabels`; nothing else does.
- **Chained actions:** `dataset_approval` chains `package_create`, `package_update`, `package_show` (a pass-through), `resource_create` and `resource_update`.
- **Templates, between our plugins:** `package/read_base.html`, `package/search.html` and `page.html` are overridden by both `mwlr_datastore` and `dataset_approval`, each on different blocks, so their order does not change what renders.
- **Templates, with core `tracking`:** CKAN's own `tracking` plugin (2.11 onwards) and `dataset_approval` both replace the same block in two templates, and neither calls `super()`:
    - `package/search.html`, block `form`: whichever is listed first supplies the search form. On the approvals environment `tracking` comes first, so the sysadmin-only sort options `dataset_approval` adds (In progress, Rejected, Review pending) do not appear.
    - `snippets/package_item.html`, block `heading_meta`: `dataset_approval`'s version replaces the base and already includes the "recent views" badge. `tracking`'s version calls `super()` and adds the badge again, so with `tracking` first a popular dataset shows it twice.
- **Helpers:** no name collisions.
- **Plugin order differs:** the approvals environment and CI list `tracking` before `dataset_approval`; the DataStore repository's `.env.example` says to add `dataset_approval` at the start.

## Decision

1. **One plugin order, recorded here and used everywhere:**

    ```text
    mwlr_datastore <restricted resources> dataset_approval tracking ... scheming_datasets ...
    ```

    Two constraints set it; the rest is today's order kept:
    - restricted resources before `dataset_approval`, so its chained actions are the outermost: nothing another plugin does to a dataset or resource reaches a user without passing its check last;
    - `dataset_approval` before core `tracking`, so the workflow's search form and listing badges are the ones that render.

    `mwlr_datastore` overlaps with neither on anything that depends on order, so it stays first. Environments that do not enable a plugin omit it; the relative order of the rest does not change.

2. **Exactly one `IPermissionLabels` implementation among our plugins.** Today that is `dataset_approval`. Restricted resources does not implement `IPermissionLabels`: labels cannot express resource-level restriction anyway. If a later feature needs dataset-level labels as well, the label logic moves into one implementation that combines the rules, rather than a second plugin implementing the interface.

3. **Resource-level access control uses chained auth functions and chained actions**, not permission labels: `resource_show`, `resource_view_show` and `resource_view_list` auth, the resource download route, and whatever `package_show` must hide from the resource list. This is also the approach of the main community extension, [ckanext-restricted](https://github.com/EnviDat/ckanext-restricted), although it replaces `package_show` and `resource_view_list` outright rather than chaining them, so it could not be adopted unmodified under rule 4.

4. **Every override of a core action or auth function is chained** (`@toolkit.chained_action`, `@toolkit.chained_auth_function`), never a plain replacement. Two plain replacements of the same action fail at startup, and a plain replacement discards core's implementation, so it has to reimplement it and keep up with every CKAN upgrade that changes it.

5. **Template overrides use `{% ckan_extends %}` and the narrowest block available, and call `super()` where they add to a block rather than replace it.** Two plugins replacing the same block is a bug to fix, not a precedence to rely on - including when the other plugin is one of CKAN's own. Where replacing is unavoidable, as with `dataset_approval`'s search form, rule 1 decides the winner and the replacing template carries what the other one would have added.

6. **The test suite runs the plugins together, in this order, and tests what they do together.** CI already loads them together on each CKAN version it tests, with `tracking` before `dataset_approval`; it moves to rule 1's order. What it lacks are tests of the combined behaviour: a dataset in review stays out of search, the workflow's sort options appear for a sysadmin, a restricted resource on an approved public dataset stays restricted.

## Alternatives considered

**Merge everything into `mwlr_datastore`.** One plugin removes ordering from the picture entirely. Rejected: switching the approval workflow off would need a feature flag of our own, where listing the plugin already does that for free, and the approval code, which carries Datopian's history and AGPL attribution, would lose its clear boundary. The composition problems do not go away either; they move inside one class where they are harder to see.

**No fixed order, each plugin defensive about the others.** Rejected: permission labels cannot be made defensive - the ignored plugin never runs - and chained actions give different results in a different order by design.

**Restricted resources as a separate package.** Possible, and nothing here prevents it later. Rejected for now for the same reason approval moved into this extension ([MWDS-400](https://manaakiwhenua.atlassian.net/browse/MWDS-400)): one release train and one place for the tests that exercise the combination.

## Consequences

- The approvals environment and CI move `tracking` after `dataset_approval`. That brings back the workflow's sort options, and also shows two CKAN 2.10 leftovers in the workflow's search form (see [dataset approval](../dataset-approval.md#open-questions), question 9). The DataStore `.env.example` comment ("add dataset_approval to the start") changes to match.
- Restricted resources has its integration points decided before its design starts: chained auth functions and actions, no permission labels, listed before `dataset_approval`.
- `dataset_approval` gets checked against these rules before it goes to testing ([dataset approval](../dataset-approval.md) lists what that check found).
- CI grows tests of the combined behaviour.

## Open questions

- **Where a plugin's fields live.** The approval fields (`publishing_status`, `chosen_visibility`, the review questions, conditions of release) sit commented out in `mwlr_datastore`'s schema, so the workflow cannot store its state (see [dataset approval](../dataset-approval.md#open-questions), question 1). The aim is that switching a plugin off hides its fields and switching it back on restores them. Constraints any answer has to meet:
    - scheming holds one schema per dataset type; a second file for the same type replaces the first, and there is no include or merge;
    - CKAN drops fields the schema does not declare, without an error, so removing a field from the schema loses its stored values the next time each dataset is edited;
    - some of these fields may describe the dataset rather than the workflow (whether a dataset needs te ao Māori review, for instance), and those may be worth keeping whether the workflow runs or not. That is for the data owners to say.

    To be proposed by the approval workflow's maintainers (Mary O'Leary, Justine Waterson), who know why each field exists. Restricted resources will face the same question for its resource fields, so the answer becomes a rule here.
- **Blueprint precedence.** `dataset_approval` registers its own `/dataset/new` and `/dataset/edit/<id>` views, which scheming and core also register. Which one serves the request depends on registration order, not on this ADR's plugin order alone. Confirm on the approvals environment and record the answer here.

## Revisit if

The restricted resources design needs dataset-level labels, a plugin moves out to its own package, or a CKAN upgrade changes how any extension point in the table above combines plugins.
