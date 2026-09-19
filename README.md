# ckanext-mwlr-datastore

The CKAN extension behind [DataStore](https://datastore.landcareresearch.co.nz), the research data catalogue run by the Bioeconomy Science Institute (formerly Manaaki Whenua – Landcare Research).

One extension, providing two plugins:

| plugin | what it does |
|---|---|
| `mwlr_datastore` | the dataset schema, its validators, the theme templates, view and download counts on dataset and resource pages, and helpers that report which environment and which build is running |
| `dataset_approval` | the dataset approval workflow: datasets stay private until an organisation admin approves them |

It is written for our catalogue rather than as a general-purpose extension, and it is published because the work is publicly funded and because the CKAN community benefits from seeing how other people solved the same problems. You are welcome to use it, fork it, or lift a single validator out of it.

## Requirements

| CKAN | supported |
|---|---|
| 2.10 | yes - what we run |
| 2.11 | not tested |
| 2.9 and earlier | no |

`mwlr_datastore` expects [`ckanext-scheming`](https://github.com/ckan/ckanext-scheming) and reads its dataset schema from `ckanext/mwlr_datastore/scheming/dataset.yaml`.

## Install

```sh
pip install git+https://github.com/manaakiwhenua/ckanext-mwlr-datastore@v1.0.0
```

Pin a tag, not a branch: two builds of the same tag should give you the same code.

Then add the plugins to your CKAN config, and point scheming at the dataset schema:

```ini
ckan.plugins = ... scheming_datasets mwlr_datastore
scheming.dataset_schemas = ckanext.mwlr_datastore:scheming/dataset.yaml
```

The view and download counts come from CKAN's own tracking; this extension only displays them. On CKAN 2.10 switch tracking on with `ckan.tracking_enabled = true`. From CKAN 2.11 it is the core `tracking` plugin instead: add it to `ckan.plugins`. A download is counted when someone clicks a download link on a dataset or resource page, as on any CKAN site; fetching the file directly, from a script or a crawler, is not counted.

## Configuration

| setting | does |
|---|---|
| `ckanext.mwlr_datastore.environment` | names a non-production environment (`dev`, `test`, `stage`). The site then shows a coloured corner marker and prefixes the browser tab, so nobody mistakes it for production. Leave it unset in production - the absence of a marker is the signal. |

| `ckanext.mwlr_datastore.readiness_path` | where the readiness endpoint is served. Defaults to `/mwlr_datastore/ready`. |

The version line in the footer is read at runtime from the running CKAN, this package's installed metadata, and the `RELEASE_VERSION`, `BUILD_NUMBER` and `GIT_COMMIT_ID` environment variables that the deploying image sets. Anything absent is omitted rather than guessed.

## Readiness

`GET /mwlr_datastore/ready` answers whether this extension finished initialising: the dataset schema is loaded by scheming, the template helpers are registered, and a template renders. It returns `200` with `"ready": true`, or `503` with each failing check named:

```json
{"ready": false, "checks": {"dataset_schema": "scheming_datasets is not loaded", "template_helpers": "ok", "template_renders": "ok"}}
```

It is meant for a readiness probe, and the contract is deliberately narrow:

- **In-memory state only.** It never calls the database or the search index, so a dependency blip does not fail readiness. With a single replica, a probe that did would turn that blip into an outage of its own making. Whether dependencies are reachable is a question for monitoring.
- **Not a check of your configuration.** Files and paths a deployment references are a property of the deployment, not of this extension; check those once at container start, before the web server comes up.
- **Not a liveness probe.** It needs a web server worker to answer, so under load it can be slow; bind liveness to something that does not queue behind real traffic, such as a TCP connect.

## Branding

There is none in this repository, on purpose. The templates reference `/logo.png`, `/favicon-32x32.png` and a couple of background images at the site root; the site that installs this extension supplies them. Ours are served from a directory outside this repository, so publishing the code does not license our logo and photographs along with it.

If you install this extension and see broken images, that is why - supply your own at those paths.

## Development

How the plugins fit together, the order to list them in and why, is in the [docs](docs/index.md#plugin-composition), with this extension's [decisions](docs/decisions/index.md).

Requires a CKAN development environment. In ours the source is bind-mounted into the CKAN container, so edits reload without a rebuild.

```sh
pip install -e .
pip install -r dev-requirements.txt
```

Run the tests against a real CKAN:

```sh
pytest --ckan-ini=test.ini ckanext/mwlr_datastore
```

## Contributing

Pull requests are welcome. Titles follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`) because they drive the version and the changelog. We squash-merge, so the pull request title is the commit that lands.

### Releasing

Every merge to `main` regenerates one open release pull request, opened by the `mwlr-release` App and titled for the next version. It needs an approval like any other pull request: approving says the changelog is right. **Merging it is the release** ([CICD-ADR-010](https://manaakiwhenua.atlassian.net/wiki/spaces/PE/pages/17284136965)): it tags the version, publishes the GitHub release with the changelog, and opens a pull request on the DataStore repository that moves the image's pin to the new tag and merges itself once its build passes, so dev and the approvals environment pick the release up on their own. Nothing merges the release pull request for you. Merge it when what it lists should ship and anything it depends on has landed - for a breaking release, the configuration that has to change first, such as a plugin list. Each new merge on `main` regenerates it and dismisses an earlier approval, so approve and merge together. To approve and let it merge once the checks pass, use `gh pr merge <number> --squash --auto`. Do not edit it by hand.

## History

This code lived at `src/ckanext-mwlr-datastore` inside a private repository holding the whole DataStore deployment, and was extracted with its history rather than restarted, so the reasoning behind the schema survives.

Two things follow from that. Commits before September 2026 were written in the context of the larger repository, so a message may describe work whose other half - a Dockerfile, a pipeline, a Kubernetes manifest - is not here. And "Bitbucket pull request N" in an old message refers to a pull request in that repository, not to anything in this one.

On 17 September 2026 the dataset approval workflow joined as the third plugin, `dataset_approval`. It came from [manaakiwhenua/ckanext-datasetapproval](https://github.com/manaakiwhenua/ckanext-datasetapproval), itself a fork of Datopian's [ckanext-datasetapproval](https://github.com/datopian/ckanext-datasetapproval), and arrived with its history: one commit standing in for the upstream work with its authors credited, then every Manaaki Whenua commit with its original author and date. The plugin's own [README](ckanext/datasetapproval/README.md) records the origin, the commit taken and what has changed since.

On 18 September 2026 the `mwlr_tracking` plugin was retired (MWDS-389). Its server-side download counter had been written as a stopgap when CKAN's own click tracking looked broken; CKAN's tracking counts downloads the standard way, so the counter went, and the two templates that show the numbers moved into `mwlr_datastore`. Configurations that list `mwlr_tracking` must drop it before upgrading.

## Licence

[AGPL-3.0-or-later](LICENSE). Note the AGPL's network clause: if you run a modified version as a public service, you must offer its source to your users.
