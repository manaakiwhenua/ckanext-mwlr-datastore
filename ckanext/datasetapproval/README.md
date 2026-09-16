# dataset_approval

The dataset approval workflow: a dataset stays private until an organisation admin has reviewed and approved it, with review types, approval and rejection feedback forms, a review history, and email to reviewers and depositors.

## Where this code came from

This plugin began as [datopian/ckanext-datasetapproval](https://github.com/datopian/ckanext-datasetapproval), written by Datopian (Sagar Ghimire and Muhammad Ismail Shahzad, 2022-2023) and published under the GNU Affero General Public License v3. Manaaki Whenua - Landcare Research forked it in 2025, at upstream commit `8da82bee3d99be32521d73220766abad8e2ed811` (3 March 2023), and developed it substantially in [manaakiwhenua/ckanext-datasetapproval](https://github.com/manaakiwhenua/ckanext-datasetapproval): CKAN 2.10 support, the review types and feedback forms, the review history, the notification emails, the reviewer and approver details, and the rest of the DataStore approval workflow (Mary O'Leary, Justine Waterson, Tomas Burleigh, 2025-2026).

On 17 September 2026 the plugin moved into this extension. The move imported the fork's history: one commit stands in for the upstream work and carries `Co-authored-by` trailers for its authors, and every Manaaki Whenua commit follows with its original author and date. The fork's last commit was `380d5feaa303` (13 August 2026); the fork is archived and kept as the record of the work under its original name.

## Modifications since the move

As the AGPL asks, the changes made here since the code was taken are noted:

- 17 September 2026: `before_search` renamed to `before_dataset_search` (CKAN 2.11 removed the old name); CSRF token added to the review form; two undefined names and a duplicate import fixed; lint clean-up. No change to what the workflow does.

Later changes are in this repository's history and changelog.

## Why it moved

Upstream stopped in July 2024 and the fork was 234 commits ahead of it, so nothing written there could go anywhere and nothing arrived from upstream. This extension already carries DataStore's templates, schema, tracking and readiness endpoint, with tests in CI and tagged releases the DataStore image pins; one extension means one release train and one place for the workflow's tests. The CKAN 2.12 upgrade needed the plugin touched anyway.

## Licence

GNU Affero General Public License v3.0 or later, as upstream. See [LICENSE](../../LICENSE) at the root of this repository. If you run a modified version as a public service, the AGPL's network clause requires that you offer its source to your users.
